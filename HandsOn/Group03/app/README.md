# BiciSmart

Aplicación web local de la asignatura de Web Semántica (UPM, Grupo 03). Usa el grafo RDF del
grupo, con BiciMAD y el Callejero de Madrid enlazados con Wikidata, para dos cosas que no se
podrían hacer solo con el CSV de BiciMAD:

- **Ruta**: dados un origen y un destino, busca la combinación más rápida andar → BiciMAD → andar.
- **Explorar**: muestra las estaciones que hay alrededor de un lugar, una calle o una estación.

Cada dato lleva una etiqueta con su fuente, y el panel «¿Por qué ontología?» explica qué aporta
cada una frente al CSV.

## Equipo

- Rodrigo Najar ([roroal23](https://github.com/roroal23))
- Shuyi Zhuang ([Yizfish](https://github.com/Yizfish))
- Alejandro Martínez ([Orlyman66](https://github.com/Orlyman66))
- Lin Wang ([Wanglin333](https://github.com/Wanglin333))
- Kai Lin Dai Wang ([Kairent8](https://github.com/Kairent8))

## Ejecutar

```bash
git clone https://github.com/UPM-Semantic-Web-LD-KG/bicismart.git
cd bicismart
uv run main.py
```

Abrir http://127.0.0.1:8000. En el primer arranque se descargan de Wikidata los datos de las
calles enlazadas y los lugares de interés de Madrid (unos 15 s), y se guardan en `data/`. En los
siguientes arranques solo se descargan las calles enlazadas que falten. Para refrescarlo todo
basta con borrar esa carpeta.

## Qué hace

### Ruta

- **Destino semántico**: puede ser una calle del Callejero, un lugar de Wikidata («Museo del
  Prado»), un tipo de lugar («un parque») o una estación. El número de la calle se ignora,
  porque el grafo modela calles y no portales. Una calle con estaciones (`bm:locatedOnStreet`)
  se usa directamente como extremo del trayecto. Si no tiene estaciones, se sitúa con sus
  coordenadas de Wikidata (`owl:sameAs` → P625), o de forma aproximada por su distrito y barrio.
- **Ruta**: solo se usan las estaciones activadas, en servicio y con bases útiles. Se prueban las 5
  más cercanas a cada extremo y se elige el par más rápido con distancias en línea recta. Después
  se piden a OSRM (FOSSGIS, OpenStreetMap) el trazado y los tiempos reales de esos tramos y de ir
  andando. Si OSRM no responde, se muestran las estimaciones marcadas como «estimado».
- **Itinerario enriquecido**: fichas de la estación de salida y de la de llegada, cada una con
  sus 3 alternativas utilizables más cercanas por si no hay bicis o huecos. Debajo, los lugares de
  interés junto al destino.

### Explorar

En la pestaña «Explorar» se elige un lugar, una calle, un tipo de lugar o una estación, o un
punto del mapa con «Explorar aquí», y un radio de 300 m, 500 m o 1 km. La app muestra:

- La lista de estaciones dentro del radio, ordenada por distancia en línea recta, con sus bases
  y su estado.
- En el mapa, el círculo del radio con esas estaciones resaltadas.

Una calle con estaciones se mide desde cada una de ellas, no desde un punto medio.

### Ficha de estación

Al pulsar una estación se abre su ficha. Muestra:

- Datos de BiciMAD: estado, bases y coordenadas.
- La calle, el distrito y el código postal (Callejero).
- A quién homenajea la calle y su imagen (Wikidata).
- Las 5 estaciones más cercanas.
- Los lugares de interés a menos de 500 m.

### Filtros del mapa

El recuadro «Estaciones» del mapa filtra por «Solo en servicio» y por «Mínimo de bases» (10, 20, 25
o 30). Los filtros se aplican a los marcadores y a la lista de Explorar, no al cálculo de rutas.
En pantallas estrechas, el recuadro aparece plegado.

### Panel «¿Por qué ontología?»

Muestra una tabla con lo que aporta cada fuente frente al CSV de BiciMAD y la lista de consultas
ejecutadas (SPARQL local, Wikidata y OSRM), con su texto.

## API

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/search?q=…` | Sugerencias: calles, lugares, tipos de lugar y estaciones |
| `GET /api/route?from=…&to=…` | Ruta en bici y andando, fichas de estación con sus alternativas y lugares cercanos |
| `GET /api/explore?ref=…&radius=500` | Centro y estaciones dentro del radio (300, 500 o 1000 m) |
| `GET /api/station/{id}` | Ficha de una estación, con las estaciones y los lugares cercanos |
| `GET /api/stations` | Todas las estaciones, para el mapa |
| `GET /api/status` | Estado de la precarga de Wikidata |

Las referencias tienen la forma `street:Calle_BravoMurillo`, `place:<QID>`, `station:<id>` o
`pt:<lat>,<lon>`. Las respuestas incluyen `queries`, las consultas que se han hecho. Hay
documentación interactiva en http://127.0.0.1:8000/docs.

## Datos

`graph/` contiene una copia de dos ficheros de la entrega del grupo. Están tomados del commit
[`0d2cd80`](https://github.com/roroal23/semantic_web_2026/tree/0d2cd80d5a2ad222af8364c1b7cb8b694a09458b/HandsOn/Group03)
de `roroal23/semantic_web_2026` (rama `Group03-Final`):

- `bicimad-with-links-updated.ttl` (de `rdf/`): estaciones, calles y enlaces a Wikidata.
- `bicismart-ontology-updated.ttl` (de `ontology/`): la ontología `bm:`.

Para actualizarlos, se copian de nuevo esos dos ficheros y se cambia el commit de este apartado.

Fuentes originales: [BiciMAD](https://datos.madrid.es) y el Callejero oficial, del portal de datos
abiertos del Ayuntamiento de Madrid, y [Wikidata](https://www.wikidata.org) (CC0).

## Estructura

- `graph/`: grafo y ontología del grupo (ver «Datos»).
- `bicismart/queries/*.rq`: consultas SPARQL sobre el grafo. `_station.rq` es el patrón común de
  estación, que las demás incluyen con `#include _station`.
- `bicismart/graph.py`: carga el grafo en Oxigraph y ejecuta las consultas. Las que no cambian se
  guardan en caché.
- `bicismart/geocode.py`: búsqueda, y resolución del origen, el destino y el centro de Explorar.
- `bicismart/routing.py`: elección de estaciones y llamadas a OSRM.
- `bicismart/enrich.py`: fichas de estación, y estaciones y lugares cercanos.
- `bicismart/explain.py`: construye las respuestas de ruta, Explorar y ficha, y los textos del
  panel «¿Por qué ontología?».
- `bicismart/geo.py`: distancias en línea recta y orden por distancia.
- `bicismart/names.py`: normalización de texto y nombres de calles y distritos.
- `bicismart/trace.py`: registro de las consultas de cada petición.
- `bicismart/errors.py`: errores que la API responde con 404 o 400.
- `bicismart/wikidata.py`: consultas a Wikidata y caché en `data/`.
- `bicismart/server.py`: API (FastAPI).
- `bicismart/static/`: web (Leaflet).

## Desarrollo

- Las convenciones y el flujo de trabajo (ramas, PRs y capturas) están en `AGENTS.md`.
- Lint: `uv run ruff check`.
