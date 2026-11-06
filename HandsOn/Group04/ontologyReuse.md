# Optional assignment – Ontology reuse

## Files

- Updated ontology: [ontology/airquality-updated.ttl](ontology/airquality-updated.ttl) (Turtle) and [ontology/airquality-updated.owl](ontology/airquality-updated.owl) (RDF/XML, same content)
- Mapping: [mappings/airquality-updated.rml](mappings/airquality-updated.rml)
- Data: [rdf/airquality-updated.ttl](rdf/airquality-updated.ttl)
- Pollutants with QUDT units: [csv/contaminantes-updated.csv](csv/contaminantes-updated.csv)

## Ontologies we looked at

We searched LOV (Linked Open Vocabularies) and the W3C recommendations for terms about sensors, observations, places and units. We used:

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
| bm:unit (text) | qudt:unit (QUDT unit IRI) |
| bm:typeCode, bm:typeName | skos:notation, skos:prefLabel |

New superclasses: bm:Station is also a geo:SpatialThing and bm:StationType is a skos:Concept.

We kept bm:observedAt, bm:measuresPollutant, bm:hasStationType and bm:isValid. SOSA links observations to sensors, not to platforms, and we do not have sensor data, so there is no direct property for "observation made at a station". We found nothing for the validity flag either.

## Data

The new RDF has 20,828 triples: the 20,817 of Hands-on 5 plus 11 qudt:unit triples, because the old mapping did not include the unit. The links to Wikidata are the same as before.
