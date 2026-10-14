# Group06

## Group members

| Name | GitHub username |
| --- | --- |
| JUNQI WENG | [jweng71](https://github.com/jweng71) |
| XIAN CHEN | [xian0223](https://github.com/xian0223) |
| LEONARDO LIN | [LeonardoLin05](https://github.com/LeonardoLin05) |
| ALEJANDRO DE LORENZO ESCRIBANO | [Pescabichillo](https://github.com/Pescabichillo) |

## Hands-on assignment 4

The RML transformation uses the existing Madrid libraries and museums datasets and the ontology in this directory.

From `HandsOn/Group06`, run:

```bash
python scripts/prepare_data.py
python scripts/generate_rdf.py
python scripts/validate_rdf.py
```

The first command converts the Windows-1252 semicolon-delimited source files into trimmed UTF-8 CSV projections. The second command uses Morph-KGC to materialize the RML mapping and serializes the resulting graph as `rdf/madrid-culture.ttl`. The last command parses the Turtle file and runs every query in `rdf/queries.sparql` against it.
