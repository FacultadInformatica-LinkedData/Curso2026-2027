# Optional assignment – Ontology reuse

## Files

- Updated ontology: [ontology/airquality-updated.ttl](ontology/airquality-updated.ttl) (Turtle) and [ontology/airquality-updated.owl](ontology/airquality-updated.owl) (RDF/XML, same content)
- Mapping: [mappings/airquality-updated.rml](mappings/airquality-updated.rml)
- Data: [rdf/airquality-updated.ttl](rdf/airquality-updated.ttl)
- Pollutants with QUDT units: [csv/contaminantes-updated.csv](csv/contaminantes-updated.csv)

## Ontologies used

We looked for vocabularies about sensors, observations, places and units. All the ones we chose are W3C recommendations or are listed in LOV (Linked Open Vocabularies):

- **SOSA** (`http://www.w3.org/ns/sosa/`) for observations. Our classes were already subclasses of SOSA classes.
- **W3C WGS84 Geo** (`http://www.w3.org/2003/01/geo/wgs84_pos#`) for coordinates.
- **schema.org** (`https://schema.org/`) for names and addresses.
- **Dublin Core Terms** (`http://purl.org/dc/terms/`) for codes.
- **DBpedia ontology** (`http://dbpedia.org/ontology/`) for the municipality.
- **QUDT** (`http://qudt.org/schema/qudt/`) for units.
- **SKOS** (`http://www.w3.org/2004/02/skos/core#`) for station types.

We also considered GeoSPARQL and vCard. We did not use them because the WGS84 properties and schema:address are simpler and fit our CSV columns directly.

## Selected terms

| Before | After |
|---|---|
| bm:dateTime | sosa:resultTime |
| bm:value | sosa:hasSimpleResult |
| bm:observesPollutant | sosa:observedProperty |
| bm:latitude, bm:longitude, bm:altitude | geo:lat, geo:long, geo:alt |
| bm:stationName, bm:municipalityName | schema:name |
| bm:pollutantName (formula) | schema:alternateName (the name goes in schema:name) |
| bm:address | schema:address |
| bm:stationCode, bm:pollutantCode, bm:municipalityCode | dct:identifier |
| bm:locatedIn | dbo:municipality |
| bm:unit (text) | qudt:hasUnit (QUDT unit IRI, e.g. `unit:MicroGM-PER-M3`) |
| bm:typeCode, bm:typeName | skos:notation, skos:prefLabel |

New superclasses: bm:Station is also a geo:SpatialThing and bm:StationType is a skos:Concept.

The reused terms are declared with the same OWL type they have in their original vocabulary. For example, skos:prefLabel is an owl:AnnotationProperty and qudt:hasUnit is an owl:ObjectProperty.

We kept bm:observedAt, bm:measuresPollutant, bm:hasStationType and bm:isValid. SOSA links observations to sensors, not to platforms, and we do not have sensor data, so there is no direct property for "observation made at a station". We found nothing for the validity flag either.

## Data generation

The RDF was generated with [RMLMapper](https://github.com/RMLio/rmlmapper-java) 8.1.0 (r380), run from `HandsOn/Group04`:

```
java -jar rmlmapper-8.1.0-r380-all.jar -m mappings/airquality-updated.rml -s turtle -o rdf/airquality-updated.ttl
```

`csv/contaminantes-updated.csv` is `csv/contaminantes-with-links.csv` with one extra column, `UNIDAD_QUDT`, which holds the QUDT unit for each pollutant.

The new RDF has 20,828 triples: the 20,817 of Hands-on 5 plus 11 qudt:hasUnit triples, because the old mapping did not include the unit. The 33 links to Wikidata are the same as before. 821 observations have no value because they are hours that were not measured yet or not valid (`ES_VALIDA` is false); this was already the case in Hands-on 5.
