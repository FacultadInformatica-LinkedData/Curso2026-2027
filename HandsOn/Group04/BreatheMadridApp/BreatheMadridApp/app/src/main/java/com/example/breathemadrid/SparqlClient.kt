package com.example.breathemadrid

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

internal data class GraphSummary(val stations: Int, val pollutants: Int, val observations: Int)
internal data class GraphStation(val uri: String, val code: String, val name: String, val category: String)

internal fun officialStationCode(mapId: String): String? =
    mapId.toIntOrNull()?.takeIf { it in 1..999 }?.let { "28079${it.toString().padStart(3, '0')}" }
internal data class GraphPollutant(val uri: String, val name: String, val unit: String?)
internal data class StationDetail(
    val station: GraphStation, val latitude: Double?, val longitude: Double?,
    val municipality: String?, val pollutants: List<GraphPollutant>,
    val total: Int, val valid: Int, val invalid: Int, val seeAlso: String?
)
internal data class MeasurementStats(
    val count: Int, val average: Double?, val minimum: Double?, val maximum: Double?,
    val first: String?, val last: String?, val unit: String?
)
internal data class MeasurementPoint(val dateTime: String, val value: Double)
internal data class MeasurementAnalysis(val stats: MeasurementStats, val points: List<MeasurementPoint>)
internal data class SemanticLink(val localUri: String, val name: String, val externalUri: String)
internal data class SemanticLinks(val pollutants: List<SemanticLink>, val stations: List<SemanticLink>)
internal data class StationObservationCount(val uri: String, val name: String, val total: Int)
internal data class GraphResult(
    val summary: GraphSummary,
    val stations: List<GraphStation>,
    val validObservationsByStation: List<StationObservationCount>,
    val validObservationsError: String?
)

internal object GraphQueries {
    private const val prefix = "PREFIX bm: <http://breathemadrid.es/ontology#>"
    private const val rdfs = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"
    private const val owl = "PREFIX owl: <http://www.w3.org/2002/07/owl#>"
    const val summary = """
        PREFIX bm: <http://breathemadrid.es/ontology#>
        SELECT ?stations ?pollutants ?observations WHERE {
          { SELECT (COUNT(DISTINCT ?station) AS ?stations)
            WHERE { ?station a bm:Station . } }
          { SELECT (COUNT(DISTINCT ?pollutant) AS ?pollutants)
            WHERE { ?pollutant a bm:Pollutant . } }
          { SELECT (COUNT(DISTINCT ?observation) AS ?observations)
            WHERE { ?observation a bm:Observation . } }
        }
    """

    const val stations = """
        PREFIX bm: <http://breathemadrid.es/ontology#>
        SELECT DISTINCT ?station ?code ?name ?type WHERE {
          VALUES ?type {
            bm:UrbanTrafficStation
            bm:UrbanBackgroundStation
            bm:SuburbanStation
          }
          ?station a bm:Station ;
                   bm:stationCode ?code ;
                   bm:stationName ?name .
          {
            ?station a ?type .
          } UNION {
            ?station bm:hasStationType ?stationType .
            VALUES (?stationType ?type) {
              (<http://breathemadrid.es/resource/stationtype/UT> bm:UrbanTrafficStation)
              (<http://breathemadrid.es/resource/stationtype/UF> bm:UrbanBackgroundStation)
              (<http://breathemadrid.es/resource/stationtype/S> bm:SuburbanStation)
            }
          }
        }
        ORDER BY ?name
    """

    const val validObservationsByStation = """
        PREFIX bm: <http://breathemadrid.es/ontology#>
        SELECT ?station ?name (COUNT(DISTINCT ?observation) AS ?total) WHERE {
          ?observation a bm:Observation ;
                       bm:observedAt ?station ;
                       bm:isValid true .
          ?station a bm:Station ;
                   bm:stationName ?name .
        }
        GROUP BY ?station ?name
        ORDER BY DESC(?total) ?name
    """

    fun stationDetail(uri: String) = """
        $prefix $rdfs
        SELECT ?lat ?lon ?municipalityName ?pollutant ?pollutantName ?unit ?seeAlso WHERE {
          VALUES ?station { <${resourceUri(uri, "station")}> }
          ?station bm:latitude ?lat ; bm:longitude ?lon ; bm:locatedIn ?municipality ;
                   bm:measuresPollutant ?pollutant .
          ?municipality bm:municipalityName ?municipalityName .
          ?pollutant bm:pollutantName ?pollutantName .
          OPTIONAL { ?pollutant bm:unit ?unit }
          OPTIONAL { ?station rdfs:seeAlso ?seeAlso }
        }
    """

    fun stationCounts(uri: String) = """
        $prefix
        SELECT (COUNT(?obs) AS ?total)
               (SUM(IF(?valid = true, 1, 0)) AS ?validCount)
               (SUM(IF(?valid = false, 1, 0)) AS ?invalidCount) WHERE {
          VALUES ?station { <${resourceUri(uri, "station")}> }
          ?obs a bm:Observation ; bm:observedAt ?station ; bm:isValid ?valid .
        }
    """

    fun stats(station: String, pollutant: String) = """
        $prefix
        SELECT (COUNT(?obs) AS ?total) (AVG(?value) AS ?average)
               (MIN(?value) AS ?minimum) (MAX(?value) AS ?maximum)
               (MIN(?dateTime) AS ?first) (MAX(?dateTime) AS ?last) WHERE {
          VALUES ?station { <${resourceUri(station, "station")}> }
          VALUES ?pollutant { <${resourceUri(pollutant, "pollutant")}> }
          ?obs a bm:Observation ; bm:observedAt ?station ;
               bm:observesPollutant ?pollutant ; bm:isValid true ;
               bm:value ?value ; bm:dateTime ?dateTime .
        }
    """

    fun series(station: String, pollutant: String) = """
        $prefix
        SELECT ?dateTime ?value WHERE {
          VALUES ?station { <${resourceUri(station, "station")}> }
          VALUES ?pollutant { <${resourceUri(pollutant, "pollutant")}> }
          ?obs a bm:Observation ; bm:observedAt ?station ;
               bm:observesPollutant ?pollutant ; bm:isValid true ;
               bm:dateTime ?dateTime ; bm:value ?value .
        } ORDER BY ?dateTime
    """

    const val pollutantLinks = """
        PREFIX bm: <http://breathemadrid.es/ontology#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?resource ?name ?external WHERE {
          ?resource a bm:Pollutant ; bm:pollutantName ?name ; owl:sameAs ?external .
        } ORDER BY ?name
    """

    const val stationLinks = """
        PREFIX bm: <http://breathemadrid.es/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?resource ?name ?external WHERE {
          ?resource a bm:Station ; bm:stationName ?name ; rdfs:seeAlso ?external .
        } ORDER BY ?name
    """
}

private fun resourceUri(uri: String, kind: String): String {
    require(Regex("^http://breathemadrid\\.es/resource/$kind/[a-z0-9-]+$").matches(uri)) {
        "URI de $kind no válida."
    }
    return uri
}

internal class SparqlClient(private val endpoint: String) {
    suspend fun load(): GraphResult = withContext(Dispatchers.IO) {
        val summaryRow = bindings(GraphQueries.summary).singleOrNull()
            ?: throw IOException("El resumen del grafo no devolvió una fila.")
        val summary = GraphSummary(
            summaryRow.value("stations").toInt(),
            summaryRow.value("pollutants").toInt(),
            summaryRow.value("observations").toInt()
        )
        val stations = bindings(GraphQueries.stations).map { row ->
            val type = row.value("type").substringAfterLast('#')
            GraphStation(row.value("station"), row.value("code"), row.value("name"), when (type) {
                "UrbanTrafficStation" -> "Urbana de tráfico"
                "UrbanBackgroundStation" -> "Urbana de fondo"
                "SuburbanStation" -> "Suburbana"
                else -> type
            })
        }
        val validObservations = runCatching {
            bindings(GraphQueries.validObservationsByStation).map { row ->
                StationObservationCount(row.value("station"), row.value("name"), row.value("total").toInt())
            }
        }
        GraphResult(summary, stations, validObservations.getOrDefault(emptyList()),
            validObservations.exceptionOrNull()?.message)
    }

    suspend fun stationDetail(station: GraphStation): StationDetail = withContext(Dispatchers.IO) {
        val rows = bindings(GraphQueries.stationDetail(station.uri))
        val first = rows.firstOrNull()
        val counts = bindings(GraphQueries.stationCounts(station.uri)).singleOrNull()
            ?: throw IOException("No se pudieron contar las observaciones de la estación.")
        StationDetail(station, first?.optionalValue("lat")?.toDoubleOrNull(),
            first?.optionalValue("lon")?.toDoubleOrNull(), first?.optionalValue("municipalityName"),
            rows.mapNotNull { row ->
                val uri = row.optionalValue("pollutant") ?: return@mapNotNull null
                GraphPollutant(uri, row.value("pollutantName"), row.optionalValue("unit"))
            }.distinctBy { it.uri }.sortedBy { it.name },
            counts.value("total").toInt(), counts.value("validCount").toInt(),
            counts.value("invalidCount").toInt(), first?.optionalValue("seeAlso"))
    }

    suspend fun analysis(station: GraphStation, pollutant: GraphPollutant): MeasurementAnalysis =
        withContext(Dispatchers.IO) {
            val row = bindings(GraphQueries.stats(station.uri, pollutant.uri)).singleOrNull()
                ?: throw IOException("La consulta estadística no devolvió una fila.")
            val stats = MeasurementStats(row.value("total").toInt(),
                row.optionalValue("average")?.toDoubleOrNull(),
                row.optionalValue("minimum")?.toDoubleOrNull(),
                row.optionalValue("maximum")?.toDoubleOrNull(),
                row.optionalValue("first"), row.optionalValue("last"), pollutant.unit)
            val points = if (stats.count == 0) emptyList() else bindings(GraphQueries.series(station.uri, pollutant.uri)).map { point ->
                MeasurementPoint(point.value("dateTime"), point.value("value").toDouble())
            }
            MeasurementAnalysis(stats, points)
        }

    suspend fun links(): SemanticLinks = withContext(Dispatchers.IO) {
        fun linksFor(query: String) = bindings(query).map { row ->
            SemanticLink(row.value("resource"), row.value("name"), row.value("external"))
        }
        SemanticLinks(linksFor(GraphQueries.pollutantLinks), linksFor(GraphQueries.stationLinks))
    }

    private fun bindings(query: String): List<JSONObject> {
        val url = URL(endpoint.trim())
        require(url.protocol == "http" || url.protocol == "https") {
            "La URL debe comenzar por http:// o https://."
        }
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 5000
            readTimeout = 10000
            doOutput = true
            setRequestProperty("Accept", "application/sparql-results+json")
            setRequestProperty("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
        }
        try {
            val body = "query=" + URLEncoder.encode(query, "UTF-8")
            connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
            if (connection.responseCode !in 200..299) {
                throw IOException("El endpoint respondió HTTP ${connection.responseCode}.")
            }
            val response = connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            val rows = JSONObject(response).getJSONObject("results").getJSONArray("bindings")
            return List(rows.length()) { rows.getJSONObject(it) }
        } finally {
            connection.disconnect()
        }
    }
}

private fun JSONObject.value(variable: String): String =
    getJSONObject(variable).getString("value")

private fun JSONObject.optionalValue(variable: String): String? =
    optJSONObject(variable)?.optString("value")
