param([string]$Endpoint = "http://localhost:3030/breathemadrid/sparql")

$prefix = "PREFIX bm: <http://breathemadrid.es/ontology#>"
$summary = @"
$prefix
SELECT ?stations ?pollutants ?observations WHERE {
  { SELECT (COUNT(DISTINCT ?station) AS ?stations) WHERE { ?station a bm:Station . } }
  { SELECT (COUNT(DISTINCT ?pollutant) AS ?pollutants) WHERE { ?pollutant a bm:Pollutant . } }
  { SELECT (COUNT(DISTINCT ?observation) AS ?observations) WHERE { ?observation a bm:Observation . } }
}
"@
$stations = @"
$prefix
SELECT DISTINCT ?station ?name ?type WHERE {
  VALUES ?type { bm:UrbanTrafficStation bm:UrbanBackgroundStation bm:SuburbanStation }
  ?station a bm:Station ; bm:stationName ?name .
  { ?station a ?type . } UNION {
    ?station bm:hasStationType ?stationType .
    VALUES (?stationType ?type) {
      (<http://breathemadrid.es/resource/stationtype/UT> bm:UrbanTrafficStation)
      (<http://breathemadrid.es/resource/stationtype/UF> bm:UrbanBackgroundStation)
      (<http://breathemadrid.es/resource/stationtype/S> bm:SuburbanStation)
    }
  }
}
ORDER BY ?name
"@
$validByStation = @"
$prefix
SELECT ?station ?name (COUNT(DISTINCT ?observation) AS ?total) WHERE {
  ?observation a bm:Observation ; bm:observedAt ?station ; bm:isValid true .
  ?station a bm:Station ; bm:stationName ?name .
}
GROUP BY ?station ?name
ORDER BY DESC(?total) ?name
"@

function Invoke-Sparql([string]$Query) {
    Invoke-RestMethod -Uri $Endpoint -Method Post -ContentType "application/x-www-form-urlencoded" -Headers @{ Accept = "application/sparql-results+json" } -Body @{ query = $Query }
}

$counts = (Invoke-Sparql $summary).results.bindings
$rows = (Invoke-Sparql $stations).results.bindings
$validRows = (Invoke-Sparql $validByStation).results.bindings
$validTotal = ($validRows | ForEach-Object { [int]$_.total.value } | Measure-Object -Sum).Sum
if ($counts.Count -ne 1 -or $counts[0].stations.value -ne "24" -or
    $counts[0].pollutants.value -ne "11" -or
    $counts[0].observations.value -ne "3024" -or $rows.Count -ne 24 -or
    $validRows.Count -ne 23 -or $validTotal -ne 2203) {
    throw "Los resultados del endpoint no coinciden con el grafo esperado."
}
Write-Output "SPARQL JSON correcto: 24 estaciones, 11 contaminantes, 3024 observaciones; 24 filas de estaciones; 2203 válidas en 23 estaciones."

$station = ($rows | Where-Object { $_.name.value -eq 'Arturo Soria' }).station.value
$localGraph = $station -eq 'http://breathemadrid.es/resource/station/28079016'
$pollutant = if ($localGraph) {
    'http://breathemadrid.es/resource/pollutant/8'
} else {
    'http://breathemadrid.es/resource/pollutant/dioxido-de-nitrogeno'
}
$detail = @"
$prefix
SELECT ?name ?lat ?lon ?municipalityName ?pollutant WHERE {
  VALUES ?station { <$station> }
  ?station bm:stationName ?name ; bm:latitude ?lat ; bm:longitude ?lon ;
           bm:locatedIn ?municipality ; bm:measuresPollutant ?pollutant .
  ?municipality bm:municipalityName ?municipalityName .
}
"@
$stationCounts = @"
$prefix
SELECT (COUNT(?obs) AS ?total)
       (SUM(IF(?valid = true, 1, 0)) AS ?validCount)
       (SUM(IF(?valid = false, 1, 0)) AS ?invalidCount) WHERE {
  VALUES ?station { <$station> }
  ?obs a bm:Observation ; bm:observedAt ?station ; bm:isValid ?valid .
}
"@
$statistics = @"
$prefix
SELECT (COUNT(?obs) AS ?total) (AVG(?value) AS ?average)
       (MIN(?value) AS ?minimum) (MAX(?value) AS ?maximum)
       (MIN(?dateTime) AS ?first) (MAX(?dateTime) AS ?last) WHERE {
  VALUES ?station { <$station> } VALUES ?pollutant { <$pollutant> }
  ?obs a bm:Observation ; bm:observedAt ?station ; bm:observesPollutant ?pollutant ;
       bm:isValid true ; bm:value ?value ; bm:dateTime ?dateTime .
}
"@
$series = @"
$prefix
SELECT ?dateTime ?value WHERE {
  VALUES ?station { <$station> } VALUES ?pollutant { <$pollutant> }
  ?obs a bm:Observation ; bm:observedAt ?station ; bm:observesPollutant ?pollutant ;
       bm:isValid true ; bm:dateTime ?dateTime ; bm:value ?value .
} ORDER BY ?dateTime
"@
$pollutantLinks = @"
$prefix
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?resource ?external WHERE { ?resource a bm:Pollutant ; owl:sameAs ?external . }
"@
$stationLinks = @"
$prefix
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?resource ?external WHERE { ?resource a bm:Station ; rdfs:seeAlso ?external . }
"@
$detailRows = (Invoke-Sparql $detail).results.bindings
$stationRow = (Invoke-Sparql $stationCounts).results.bindings[0]
$statsRow = (Invoke-Sparql $statistics).results.bindings[0]
$seriesRows = (Invoke-Sparql $series).results.bindings
$pollutantLinkRows = (Invoke-Sparql $pollutantLinks).results.bindings
$stationLinkRows = (Invoke-Sparql $stationLinks).results.bindings
if ($detailRows.Count -ne 4 -or $detailRows[0].name.value -ne 'Arturo Soria' -or
    $stationRow.total.value -ne '96' -or $stationRow.validCount.value -ne '72' -or
    $stationRow.invalidCount.value -ne '24' -or $statsRow.total.value -ne '18' -or
    $seriesRows.Count -ne 18) {
    throw 'El detalle, análisis, serie o enlaces no coinciden con el grafo esperado.'
}
if (-not $localGraph -and ($pollutantLinkRows.Count -ne 11 -or $stationLinkRows.Count -ne 21)) {
    throw 'Los enlaces externos no coinciden con el grafo enlazado esperado.'
}
Write-Output "Explorador correcto: Arturo Soria 96/72/24; NO2 18 puntos; $($pollutantLinkRows.Count) enlaces de contaminantes y $($stationLinkRows.Count) de estaciones."
