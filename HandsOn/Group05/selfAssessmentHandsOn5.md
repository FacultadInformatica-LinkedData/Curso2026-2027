# Hands-on assignment 5 – Self assessment (Group05)

## Checklist

**Every RDF file:**

- [x] Has at least one owl:sameAs property that links to another dataset

**Every owl:sameAs property:**

- [x] Links a resource in the dataset with another resource in an external dataset

**The SPARQL file:**

- [x] Includes at least 1 query
- [x] Contains queries that retrieve the data that would be needed in the application

**Every SPARQL query:**

- [x] Makes use of the ontology
- [x] Returns a non-empty result
- [x] Makes use of the owl:sameAs links

## Comments on the self-assessment

### Entregables

| Fichero | Descripción |
| :--- | :--- |
| `openrefine/polideportivos-with-links.json` | Historial de operaciones de OpenRefine (52) para reconciliar con Wikidata. |
| `csv/polideportivos-with-links.csv` | CSV del Hands-On 3 con dos columnas nuevas: `WIKIDATA-DISTRITO` y `WIKIDATA-CENTRO`. |
| `mappings/polideportivos-with-links.rml` | Mappings del Hands-On 4 actualizados con `owl:sameAs`. |
| `rdf/polideportivos-with-links.ttl` | Datos enlazados en Turtle (1024 tripletas, 45 `owl:sameAs`). |
| `rdf/queries-with-links.sparql` | 7 consultas que usan la ontología y los enlaces. |


### Consultas

Todas devuelven resultados sobre `rdf/polideportivos-with-links.ttl`: número de enlaces por clase, distritos con su entidad de Wikidata, centros con su distrito enlazado (ficha), centros enlazados con coordenadas (mapa), centros por distrito, centros con piscina enlazados y centros de un distrito buscado por su URI de Wikidata.

### Observaciones

