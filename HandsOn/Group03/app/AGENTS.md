# BiciSmart

App web local en Python para la asignatura de Web Semántica (Grupo 03). Dados un origen y un
destino, busca la mejor combinación andar → BiciMAD → andar usando el grafo RDF del grupo:
BiciMAD y el Callejero de Madrid, enlazados con Wikidata. El funcionamiento y la estructura
están en el README.

## Objetivo

La app tiene que demostrar el valor de la ontología: hacer algo que no se podría con un solo
dataset. Cada funcionalidad debe apoyarse en el grafo (enlace estación → calle, datos del
Callejero, `owl:sameAs` a Wikidata) y mostrarlo:

- Cada dato de la interfaz lleva su fuente: BiciMAD, Callejero, Wikidata u OSRM.
- El panel «¿Por qué ontología?» muestra qué no se podría obtener solo con el CSV de BiciMAD
  y las consultas ejecutadas. Toda consulta nueva, local o externa, debe pasar por
  `trace.record` para que aparezca en él (`graph.query` ya lo hace).

## Decisiones tomadas

- **No se extiende la ontología.** Se trabaja con lo que tiene el grafo, aunque se pierda
  exactitud. El grafo modela calles, no portales: «Bravo Murillo 120» se resuelve como la
  calle Bravo Murillo.
- **Es una demo.** No hace falta preocuparse por concurrencia, escalado ni limitadores.
- **Los enlaces `owl:sameAs` de calles a Wikidata se hicieron a mano.** No propongas
  ampliarlos ni automatizarlos.

## Convenciones

- Identificadores y código en inglés; docstrings, comentarios y textos de la interfaz en español.
- Las consultas SPARQL al grafo van en `bicismart/queries/*.rq`, con parámetros `$nombre`
  (ver `graph.query`), no escritas dentro del Python.
- Python 3.12 y dependencias con `uv` (`uv add`).

## Ejecutar y comprobar

- `uv run main.py` y abrir http://127.0.0.1:8000.
- No hay tests automáticos. Para comprobar un cambio, usa `fastapi.testclient.TestClient`
  contra `bicismart.server.app` y prueba la búsqueda, las rutas y las fichas de estación.
  Con `with TestClient(app)` también se ejecuta la precarga de Wikidata.

## Cambios y PRs

- Todo cambio va en una rama creada desde `main` y se propone con un PR contra `main`. No hagas
  commits directamente en `main` ni fusiones PRs: los revisa y los fusiona el equipo.
- Título, descripción y mensajes de commit en español. La descripción explica qué cambia, cómo
  se ha probado y sus limitaciones.
- Siempre que sea posible, y sobre todo si cambia algo visible, añade capturas en una sección
  «Capturas» de la descripción:
  - Hazlas con Selenium y Firefox headless, con el servidor en un puerto distinto del 8000.
  - Súbelas a la rama `screenshots`, que no comparte historia con `main`, en la carpeta
    `pr-<número>/`. Nunca las subas a `main` ni a la rama del PR.
  - Enlázalas con `<URL del repositorio>/blob/screenshots/pr-<número>/<fichero>.png?raw=true`.

## Datos

- `graph/` contiene lo que necesita la app: el grafo (`bicimad-with-links-updated.ttl`) y la
  ontología (`bicismart-ontology-updated.ttl`).
- `data/` es la caché de Wikidata que genera la app. No se edita a mano; borrarla fuerza a
  descargarla de nuevo.

## Servicios externos

- **Wikidata** (`query.wikidata.org`): calles enlazadas y lugares de interés, con caché en `data/`.
- **OSRM de FOSSGIS** (`routing.openstreetmap.de`): servicio público con límites de uso.
  Haz pocas peticiones y nunca en ráfaga: una prueba en ráfaga dejó la IP bloqueada un
  tiempo. Si no responde, la app usa una estimación en línea recta.
