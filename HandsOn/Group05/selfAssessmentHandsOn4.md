# Hands-on assignment 4 – Self assessment (Group05)

## Checklist

**Every RDF file:**

- [x] Uses the .ttl extension
- [x] Is serialized in the Turtle format
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

## Comments on the self-assessment

### Entregables

| Fichero | Descripción |
| :--- | :--- |
| `mappings/polideportivos.rml` | Mappings RML (sintaxis `http://w3id.org/rml/` + RML-FNML con funciones GREL). |
| `mappings/polideportivos.yml` | Mismas reglas en YARRRML (opcional). Genera exactamente las mismas 979 tripletas. |
| `rdf/polideportivos.ttl` | Datos transformados a RDF en sintaxis Turtle. |
| `rdf/queries.sparql` | 10 consultas SPARQL para verificar los datos. |

La transformación se ha realizado con morph-kgc 2.10 ejecutado desde `HandsOn/Group05` (la ruta del CSV en los mappings es relativa a ese directorio).

### Resultado

- 979 tripletas: 82 individuos `:SportsCenter` y 21 individuos `:District` (los 21 distritos de Madrid).
- URIs según la estrategia de nombrado de `analysis.html`:
  - Centros: `http://smartcity.linkeddata.es/sports/resource/SportsCenter/{URI-CENTRO}`, por ejemplo `SportsCenter/MarquesDeSamaranch`.
  - Distritos: `http://smartcity.linkeddata.es/sports/resource/District/{URI-DISTRITO}`, por ejemplo `District/PuenteDeVallecas`. El enlace `:locatedInDistrict` usa la misma plantilla, así que el centro y el distrito siempre apuntan a la misma URI.
  - Actualización tras el feedback (`HO_evaluation_1.md`): en la entrega original los centros usaban el `PK` numérico (`SportsCenter/10183549`) y los distritos un slug en minúsculas (`District/puente-de-vallecas`). Ahora todas las URIs de individuos son legibles y empiezan por mayúscula. Los identificadores se generan en OpenRefine (columnas `URI-CENTRO` y `URI-DISTRITO`, ver `selfAssessmentHandsOn3.md`) y el mapping ya no necesita funciones GREL para construir la URI del distrito. El `PK` se conserva como dato con `:pk`. Se han regenerado `rdf/polideportivos.ttl` (979 tripletas) y `rdf/polideportivos-with-links.ttl` (1024 tripletas): el contenido es el mismo y las consultas SPARQL devuelven los mismos resultados.
- Todos los individuos tienen `rdf:type` y `rdfs:label` (`@es`). La consulta Q4 lo comprueba y no devuelve resultados.
- Tipos de datos: `:pk` es `xsd:integer`; `geo:lat`/`geo:long` son `xsd:float` (igual que en `ontology-example.ttl`); el resto son `xsd:string`. Teléfonos y códigos de accesibilidad se guardan como texto aunque sean dígitos, porque no son cantidades.
- Columnas multivaluadas: `TELEFONO` y `EMAIL` (separadas por `;` en el Hands-On 3) y `ACCESIBILIDAD` (separada por `,`) se dividen con `grel:string_split`, de modo que se genera un literal por valor (p. ej. 16 centros tienen más de un teléfono).
- Las celdas vacías no generan tripletas (dos centros no tienen teléfono ni email: Fernando Carro - Las Rosas y Fúcar).

### Observaciones

- Además de las clases y propiedades de nuestra ontología (`:SportsCenter`, `:District`, `:pk`, `:locatedInDistrict`, `:equipmentDescription`, `:accessibilityInfo`, `:transportInfo`, `:telephone`, `:email`), se reutilizan `rdfs:label` y `geo:lat`/`geo:long` (WGS84), tal y como se indica en `analysis.html` y en `ontology-example.ttl`.
- El RML usa la sintaxis nueva de RML (`http://w3id.org/rml/`) porque morph-kgc solo soporta funciones (RML-FNML) con esa sintaxis; la plantilla de la asignatura usa la sintaxis antigua (`rr:` / `semweb.mmlab.be`). Se ha probado con morph-kgc 2.10.
- Columnas del CSV que todavía no tienen propiedad en la ontología y, por tanto, no se transforman: `HORARIO`, `DESCRIPCION`, la dirección postal (`NOMBRE-VIA`, `NUM`, `CODIGO-POSTAL`...), `BARRIO`, `COD-DISTRITO`, `COORDENADA-X/Y`, `CONTENT-URL`, `FAX` y `TIPO`. Se podrán incorporar si se amplía la ontología (p. ej. una clase para barrios, como prevé la estrategia de nombrado, o `TIPO` como subclase de `:SportsCenter`).
- `ACCESIBILIDAD` se mantiene como código (0, 1, 2, 4, 5, 6) porque el dataset no incluye su significado.
