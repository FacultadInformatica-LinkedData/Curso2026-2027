# Hands-on assignment 4 - Self-assessment

## Deliverables

- [x] RML mapping in `mappings/madrid-culture.rml`
- [x] Optional YARRRML mapping in `mappings/madrid-culture.yml`
- [x] Generated RDF in Turtle syntax in `rdf/madrid-culture.ttl`
- [x] Verification queries in `rdf/queries.sparql`

## Every RDF file

- [x] Uses the `.ttl` extension.
- [x] Is serialized in Turtle syntax.
- [x] Follows the resource naming strategy defined in `analysis.html`.
- [x] Uses the same class and property URIs as `ontology/ontology.ttl` and the reused RDF, RDFS and Schema.org vocabularies.

## Every URI in the RDF file

- [x] Follows a meaningful class-specific pattern under `https://w3id.org/madrid-culture/resource/`.
- [x] Uses the stable municipal `PK` or the documented district/neighborhood codes rather than a generated row number.
- [x] Is represented as an IRI, not as a string literal.
- [x] Has no spaces or repeated slashes in the URI path.

## Every individual in the RDF file

- [x] Has an explicit RDF type.
- [x] Has an `rdfs:label` in Spanish.
- [x] Linked addresses, districts and neighborhoods are also described resources rather than dangling IRIs.

## Every value in the RDF file

- [x] Source values are decoded from Windows-1252, HTML entities are decoded, whitespace is normalized and surrounding spaces are removed by `scripts/prepare_data.py`.
- [x] Empty CSV cells do not generate empty RDF literals.
- [x] Latitude and longitude values use `xsd:decimal`.
- [x] Postal codes, telephone numbers and local classifications use `xsd:string`, preserving leading zeros and formatting.
- [x] Spanish names and descriptions use the `es` language tag.
- [x] Official web pages are IRIs.

## Transformation and validation evidence

- The input contains 52 libraries and 68 museums.
- The preprocessing step produces UTF-8 CSV files for 52 libraries, 68 museums, 21 districts and 66 neighborhoods.
- Morph-KGC generates 327 individuals and 2,502 unique RDF triples.
- The Turtle output was parsed successfully after generation.
- Queries Q4-Q7 in `rdf/queries.sparql` return no rows; they check missing labels, dangling resource links, incorrect datatypes, malformed URIs and empty literals.

## Reflection

This assignment made the separation between source data and RDF structure explicit. The logical sources select rows from the prepared CSV files, subject maps create stable IRIs following the Group06 naming strategy, and predicate-object maps assign types, labels, typed values and links. Separate mappings for addresses, districts and neighborhoods turn repeated tabular values into reusable resources. The YARRRML file expresses the same rules more compactly, while the RML file is the executable mapping used by Morph-KGC.
