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
| Station category codes and names | `skos:notation` and `skos:prefLabel` on the three station subclasses |

New superclasses: bm:Station is also a geo:SpatialThing. Urban traffic, urban background and suburban stations are subclasses of bm:Station.

The reused terms are declared with the same OWL type they have in their original vocabulary. For example, skos:prefLabel is an owl:AnnotationProperty and qudt:hasUnit is an owl:ObjectProperty.

We kept bm:observedAt, bm:measuresPollutant and bm:isValid. SOSA links observations to sensors, not to platforms, and we do not have sensor data, so there is no direct property for "observation made at a station". We found nothing for the validity flag either. The former `bm:StationType` individuals and `bm:hasStationType` links were replaced by explicit `rdf:type` assertions to `bm:UrbanTrafficStation`, `bm:UrbanBackgroundStation` and `bm:SuburbanStation`. The source codes UT, UF and S are preserved as class metadata with `skos:notation`.

## Data generation

Before running any mapping, prepare the URI columns from the existing OpenRefine outputs:

```
python scripts/prepare_uri_csv.py
```

This deterministic step uses fixed official-code-to-slug tables for the 24 stations and 11 pollutants, and a fixed code-to-class mapping for the three station categories. It writes six staged CSV files under `csv/uri/`; it does not alter the source CSVs or OpenRefine outputs. All three RML mappings use these staged files, so references to the same individual always receive the same URI. Observation identifiers include the technique from `PUNTO_MUESTREO`, and the complete original sampling point is retained as `bm:samplingPointCode` (`bm:Observation` domain, `xsd:string` range). Official station, pollutant and municipality codes remain in their existing RDF properties; category codes are metadata on classes.

Regenerate the five RDF files from `HandsOn/Group04` with RMLMapper:

```
java -jar rmlmapper-8.1.0-r380-all.jar -m mappings/airquality.rml -s turtle -o rdf/airquality.ttl
java -jar rmlmapper-8.1.0-r380-all.jar -m mappings/airquality-with-links.rml -s turtle -o rdf/airquality-with-links.ttl
java -jar rmlmapper-8.1.0-r380-all.jar -m mappings/airquality-updated.rml -s turtle -o rdf/airquality-updated.ttl
```

RMLMapper 8.1.0 does not expose N-Triples as a `-s` format. Serialize the two generated Turtle graphs as N-Triples with RDFLib:

```
python scripts/serialize_nt.py
```

The RDF was generated with [RMLMapper](https://github.com/RMLio/rmlmapper-java) 8.1.0 (r380), run from `HandsOn/Group04`:

```
java -jar rmlmapper-8.1.0-r380-all.jar -m mappings/airquality-updated.rml -s turtle -o rdf/airquality-updated.ttl
```

`csv/contaminantes-updated.csv` is `csv/contaminantes-with-links.csv` with one extra column, `UNIDAD_QUDT`, which holds the QUDT unit for each pollutant.

Before the URI migration, the updated RDF had 20,828 triples: the 20,817 of Hands-on 5 plus 11 `qudt:hasUnit` triples. The URI migration added 3,024 triples, one original sampling point code per observation, yielding 23,852. Replacing the three station-type individuals with explicit station subclass types yields 23,840 triples: 12 triples describing the old individuals and 24 `bm:hasStationType` links are removed, while 24 subclass `rdf:type` triples are added. The 33 links to Wikidata are unchanged. 821 observations have no value because they are hours that were not measured yet or not valid (`ES_VALIDA` is false); this was already the case in Hands-on 5.
