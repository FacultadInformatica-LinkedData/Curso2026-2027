# Hands-on assignment 4 – Self assessment

## Checklist

**Every RDF file:**

- [x] Uses the .nt extension
- [x] Is serialized in the NTriples format
- [x] Follows the resource naming strategy
- [x] Uses class and property URIs that are the same as those used in the ontology

**Every URI in the RDF files:**

- [x] Is "readable" and has some meaning (e.g., it is not an auto-increased integer) 
- [x] Is not encoded as a string
- [x] Does not contain a double slash (i.e., “//”)

**Every individual in the RDF files:**

- [x] Has a label with the name of the individual
- [x] Has a type

**Every value in the RDF files:**

- [x] Is trimmed
- [x] Is properly encoded (e.g., dates, booleans)
- [x] Includes its datatype
- [x] Uses the correct datatype (e.g., values of 0-1 may be booleans and not integers, not every string made of numbers is a number)

## Additional checks

**The "mappings" directory:**

- [x] Contains an RML file (`airquality.rml`) with the mappings for the selected CSV datasets to RDF.

**The "rdf" directory:**

- [x] Contains an RDF file in the Turtle syntax (`airquality.ttl`) with the transformed data.
- [x] Contains an RDF file in the N-Triples syntax (`airquality.nt`) with the transformed data.
- [x] Contains a SPARQL file (`queries.sparql`) with queries to verify the transformed data.

**The RML mapping:**

- [x] Maps station metadata, including station codes, names, addresses, coordinates, altitude and explicit station subclass types.
- [x] Links the municipality to Wikidata using `owl:sameAs`.
- [x] Maps hourly air quality observations and links them to stations via `bm:observedAt`, and to pollutants via `bm:observesPollutant`.
- [x] Links stations to monitored pollutants via `bm:measuresPollutant`.
- [x] Maps pollutant metadata from `csv/contaminantes.csv`.
- [x] Handles invalid measurements by omitting `bm:value` when `VALOR_MEDICION` is empty.

**Data verification:**

- [x] Includes SPARQL queries to check the number of stations and observations.
- [x] Includes queries to verify the presence of mandatory properties and the expected literal datatypes.
- [x] Includes queries to verify the links between observations, monitoring stations and pollutants.
- [x] Runs the SPARQL queries against the generated RDF and reviews the results.

## Comments on the self-assessment

- **RDF files.** The assignment asks for a Turtle file and this checklist asks for N-Triples, so both are delivered: `rdf/airquality.ttl` and `rdf/airquality.nt` contain exactly the same 23,797 triples after the URI and station category migrations. RMLMapper v8.1.0 generates the Turtle file from `mappings/airquality.rml`; `scripts/serialize_nt.py` serializes the same graph as N-Triples.
- **Readable URIs.** Individuals use fixed Spanish slugs based on official codes (e.g., `resource/station/plaza-de-espana`, `resource/pollutant/dioxido-de-nitrogeno`). The official station and pollutant codes remain in RDF properties. Observation URIs include the sampling technique; the complete source sampling point is retained as `bm:samplingPointCode`. The URI strategy is documented in `analysis.html`.
- **Station categories.** `UT`, `UF` and `S` are represented by the ontology subclasses `bm:UrbanTrafficStation`, `bm:UrbanBackgroundStation` and `bm:SuburbanStation`. All 24 station individuals have exactly one of these explicit types; the original codes are recorded as `skos:notation` on the classes.
- **String datatypes.** Every literal has its datatype declared in the mapping (`rr:datatype`). Text literals appear without an explicit `^^xsd:string` in the output because, in RDF 1.1, a literal without a datatype is an `xsd:string`, and RMLMapper omits it.
- **Invalid observations.** The 821 observations marked as not valid (`VALIDEZ = N`) have `bm:isValid false` and no `bm:value`: the original `0` was only a placeholder, so it was removed during data cleaning (Hands-on 3). Query Q11 checks this.
- **Auxiliary data.** `csv/contaminantes.csv` contains the names and units of the 11 pollutant codes in the dataset, taken from the official data interpretation document of the Madrid air quality dataset. The hour `24` of the source data was converted into `00:00` of the following day (`FECHA_HORA` column) so that it is a valid `xsd:dateTime`.
- **YARRRML.** The optional YARRRML file was not delivered; the mappings are only provided in RML.
