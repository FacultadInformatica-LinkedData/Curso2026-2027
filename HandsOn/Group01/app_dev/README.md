# Madrid Smart City (aplicación)

Aplicación web que explota el grafo de conocimiento de alojamientos turísticos del Grupo 01.

- **GraphDB** guarda `ontology/ontology-updated.ttl` + `rdf/data-updated.ttl` en el repositorio
  `alojamientos-turisticos` (ruleset *RDFS (Optimized)*, con *Disable owl:sameAs* marcado).
- **Wikidata** aporta el contexto de cada municipio (coordenadas P625, población P1082, imagen P18),
  al que se llega siguiendo los enlaces `owl:sameAs` del grafo.
- `server.py` sirve la página y reenvía las consultas SPARQL a GraphDB y a Wikidata. Así el
  navegador no necesita CORS y Wikidata recibe un *User-Agent* identificado (sin él, bloquea las
  consultas).

## Cómo arrancarla

1. Abrir **GraphDB Desktop** (http://localhost:7200) con el repositorio `alojamientos-turisticos`
   creado y los dos `.ttl` cargados (ver "Preparar GraphDB" más abajo).
2. En una terminal, dentro de esta carpeta: `python server.py`
3. Abrir http://localhost:8000 en el navegador.

Hace falta conexión a internet para el mapa (OpenStreetMap), las fuentes y los datos de Wikidata.
Para pararla: `Ctrl + C` en la terminal.

## Preparar GraphDB (solo la primera vez en cada ordenador)

1. Instalar GraphDB Desktop (gratuito, web de Ontotext) y abrir el Workbench (http://localhost:7200).
2. *Setup → Repositories → Create new repository → GraphDB Repository*:
   - Repository ID: `alojamientos-turisticos`
   - Ruleset: `RDFS (Optimized)`
   - Marcar *Disable owl:sameAs* (si no, GraphDB fusiona cada municipio con su entidad de Wikidata
     y los resultados salen duplicados).
3. Seleccionar el repositorio arriba a la derecha → *Import → Upload RDF files* → subir
   `ontology/ontology-updated.ttl` y `rdf/data-updated.ttl` con las opciones por defecto.
4. Comprobación: deben aparecer 87.477 + 87 triples importados.

## Páginas

- `index.html` (búsqueda): filtros por tipo de alojamiento (incluidas agrupaciones que solo
  funcionan gracias a la inferencia RDFS: todos los alojamientos, alojamientos rurales y todos los
  hoteles = `schema:Hotel`), categorías exactas (selección múltiple, más "sin categoría"),
  municipio, código postal y nombre; resultados en tarjetas paginadas (50 por página); mapa de
  municipios (coordenadas de Wikidata) con círculos proporcionales al número de alojamientos que
  cumplen los filtros (al pulsar uno, se filtra por él). Los filtros se guardan en la URL, por eso
  al volver de una ficha se recuperan.
- `ficha.html?id=<signatura>` (página de un alojamiento): datos de GraphDB y contexto del
  municipio desde Wikidata (foto, población, mapa y enlace a su página de Wikidata), más otros alojamientos
  del mismo municipio.
- El botón **SPARQL** (abajo a la derecha, en las dos páginas) abre un panel con todas las consultas
  que se han lanzado para la pantalla actual, a GraphDB y a Wikidata, con botón de copiar.

## Archivos

- `server.py`: servidor local y proxy hacia GraphDB y Wikidata (solo librería estándar de Python).
- `common.js`: acceso SPARQL compartido, nombres en español de los tipos, colores e iconos.
- `index.html` + `app.js`: página de búsqueda.
- `ficha.html` + `ficha.js`: página de cada alojamiento.
- `style.css`: estilos de las dos páginas.

## Limitaciones

- Los datos de origen no incluyen coordenadas de cada alojamiento, solo su dirección, por eso el
  mapa trabaja a nivel de municipio.
- 19 alojamientos no indican municipio en el registro, así que no tienen enlace a Wikidata.
