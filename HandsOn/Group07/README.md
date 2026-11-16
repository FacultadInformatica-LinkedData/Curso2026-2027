# Group 07

## Authors

| Name | GitHub Username |
|---|---|
| Chengjian Zhou | [@ChengJianZhou](https://github.com/ChengJianZhou) |
| Jaime Martinez-Carande Florez | [@nunt2](https://github.com/nunt2) |
| Mateo Cuñarro Alfonsín | [@minimoai33](https://github.com/minimoai33) |
| Denis Andrei Cosor Strimbeanu | [@denisandrei-byte](https://github.com/denisandrei-byte) |
| Mateo Rodríguez Chinchilla | [@Mathew017](https://github.com/Mathew017) |

## Project

Madrid urban environment: drinking fountains, benches, public toilets and parks, linked to the districts and neighborhoods where they are located.

## Deliverables

- `analysis.html`: dataset analysis and resource naming strategy.
- `ontology/ontology.ttl`: final ontology.
- `ontology/ontology-example.ttl`: sample individuals in the final model.
- `mappings/mapping_final.rml`: final RML mapping.
- `rdf/datos.ttl`: RDF graph generated with the final mapping.
- `rdf/queries.sparql`: example and validation queries.
- `openrefine/`: OpenRefine operation histories.
- `csv/with-labels/`: input CSVs used by the final mapping.

## Reproducing the RDF

The final mapping reads the CSVs in `csv/with-labels/` and writes `rdf/datos.ttl`:

```bash
java -Xmx4g -jar rmlmapper-8.1.0-r380-all.jar \
  -m Group07/mappings/mapping_final.rml \
  -o Group07/rdf/datos.ttl \
  -s turtle
```

`mappings/mapping_new.rml` is the original mapping and is kept for reference. `mappings/mapping_v2.rml` is a superseded draft.