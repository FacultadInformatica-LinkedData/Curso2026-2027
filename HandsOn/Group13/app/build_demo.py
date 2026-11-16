#!/usr/bin/env python3
"""Genera app/educa-madrid.html a partir del grafo local.

El HTML se abre con doble clic. Lleva los centros y el resultado de las
consultas dentro; no hace falta Python para verlo.
"""

import json
import re
import urllib.parse
from pathlib import Path

from rdflib import Graph

ROOT = Path(__file__).resolve().parent
RDF_PATH = ROOT / "WebSemantica" / "rdf" / "centros-educativos-with-links.ttl"
OUT_PATH = ROOT / "educa-madrid.html"

QUERIES = [
    (
        "1. Total de centros educativos por distrito y su enlace owl:sameAs a Wikidata",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?distrito (COUNT(DISTINCT ?centro) AS ?totalCentros) ?wikidataDistrito
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri .
    ?distUri rdfs:label ?distrito ;
             owl:sameAs ?wikidataDistrito .
}
GROUP BY ?distrito ?wikidataDistrito
ORDER BY DESC(?totalCentros)""",
    ),
    (
        "2. Top 20 barrios con más centros educativos y su entidad en Wikidata",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?barrio ?distrito (COUNT(DISTINCT ?centro) AS ?totalCentros) ?wikidataBarrio
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:hasAddress ?addr .
    ?addr ont:inNeighborhood ?barrioUri ;
          ont:inDistrict ?distUri .
    ?barrioUri rdfs:label ?barrio ;
               owl:sameAs ?wikidataBarrio .
    ?distUri rdfs:label ?distrito .
}
GROUP BY ?barrio ?distrito ?wikidataBarrio
ORDER BY DESC(?totalCentros)
LIMIT 20""",
    ),
    (
        "3. Distribución de centros según su código de accesibilidad",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>

SELECT ?codigoAccesibilidad (COUNT(DISTINCT ?centro) AS ?totalCentros)
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:accessibilityCode ?codigoAccesibilidad .
}
GROUP BY ?codigoAccesibilidad
ORDER BY DESC(?totalCentros)""",
    ),
    (
        "4. Centros totalmente adaptados (accesibilidad = '3') con sus datos de contacto",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?telefono ?email
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:accessibilityCode "3" ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    OPTIONAL { ?centro ont:telephone ?telefono . }
    OPTIONAL { ?centro ont:email ?email . }
}
ORDER BY ?distrito ?nombre""",
    ),
    (
        "5. Centros que disponen simultáneamente de Comedor y Horario ampliado",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?equipamiento
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:equipment ?equipamiento ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    FILTER(CONTAINS(LCASE(?equipamiento), "comedor") && CONTAINS(LCASE(?equipamiento), "horario ampliado"))
}
ORDER BY ?distrito ?nombre""",
    ),
    (
        "6. Centros con enseñanza bilingüe (filtrando por descripción)",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?barrio ?descripcion
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:description ?descripcion ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
    FILTER(CONTAINS(LCASE(?descripcion), "bilingüe"))
}
ORDER BY ?distrito ?nombre""",
    ),
    (
        "7. Centros con conexión directa a Cercanías Renfe",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nombre ?distrito ?transporte
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:transportation ?transporte ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri .
    ?distUri rdfs:label ?distrito .
    FILTER(CONTAINS(LCASE(?transporte), "renfe") || CONTAINS(LCASE(?transporte), "cercanías"))
}
ORDER BY ?distrito ?nombre""",
    ),
    (
        "8. Conteo de centros por tipología (ont:centerType)",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>

SELECT ?tipo (COUNT(DISTINCT ?centro) AS ?totalCentros)
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerType ?tipo .
}
GROUP BY ?tipo
ORDER BY DESC(?totalCentros)""",
    ),
    (
        "9. Relación jerárquica de Barrios y Distritos con sus respectivas URIs de Wikidata",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?distrito ?wikidataDistrito ?barrio ?wikidataBarrio
WHERE {
    ?barrioUri a ont:Neighborhood ;
               rdfs:label ?barrio ;
               ont:belongsToDistrict ?distUri ;
               owl:sameAs ?wikidataBarrio .
    ?distUri rdfs:label ?distrito ;
             owl:sameAs ?wikidataDistrito .
}
ORDER BY ?distrito ?barrio""",
    ),
    (
        "10. Muestra de centros con nombre, identificador, distrito y barrio",
        """PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?centro ?nombre ?pk ?distrito ?barrio
WHERE {
    ?centro a ont:EducationalCenter ;
            ont:centerName ?nombre ;
            ont:pk ?pk ;
            ont:hasAddress ?addr .
    ?addr ont:inDistrict ?distUri ;
          ont:inNeighborhood ?barrioUri .
    ?distUri rdfs:label ?distrito .
    ?barrioUri rdfs:label ?barrio .
}
ORDER BY ?nombre
LIMIT 25""",
    ),
]

CENTERS_QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?centro ?nombre ?tipo ?desc ?horario ?equipamiento ?transporte ?telefono ?email ?url ?accesibilidad
       ?streetType ?streetName ?streetNumber ?postalCode
       (SAMPLE(?latVal) AS ?lat) (SAMPLE(?longVal) AS ?long)
       ?distritoUri ?distritoLabel ?wikidataDistrito
       ?barrioUri ?barrioLabel ?wikidataBarrio
WHERE {
    ?centro rdf:type ont:EducationalCenter ;
            ont:centerName ?nombre .
    OPTIONAL { ?centro ont:centerType ?tipo . }
    OPTIONAL { ?centro ont:description ?desc . }
    OPTIONAL { ?centro ont:schedule ?horario . }
    OPTIONAL { ?centro ont:equipment ?equipamiento . }
    OPTIONAL { ?centro ont:transportation ?transporte . }
    OPTIONAL { ?centro ont:telephone ?telefono . }
    OPTIONAL { ?centro ont:email ?email . }
    OPTIONAL { ?centro ont:contentUrl ?url . }
    OPTIONAL { ?centro ont:accessibilityCode ?accesibilidad . }
    OPTIONAL {
        ?centro ont:hasAddress ?addr .
        OPTIONAL { ?addr ont:streetType ?streetType . }
        OPTIONAL { ?addr ont:streetName ?streetName . }
        OPTIONAL { ?addr ont:longitude ?longVal . }
        OPTIONAL { ?addr ont:latitude ?latVal . }
        OPTIONAL { ?addr ont:streetNumber ?streetNumber . }
        OPTIONAL { ?addr ont:postalCode ?postalCode . }
        OPTIONAL {
            ?addr ont:inDistrict ?distritoUri .
            OPTIONAL { ?distritoUri rdfs:label ?distritoLabel . }
            OPTIONAL { ?distritoUri owl:sameAs ?wikidataDistrito . }
        }
        OPTIONAL {
            ?addr ont:inNeighborhood ?barrioUri .
            OPTIONAL { ?barrioUri rdfs:label ?barrioLabel . }
            OPTIONAL { ?barrioUri owl:sameAs ?wikidataBarrio . }
        }
    }
}
GROUP BY ?centro ?nombre ?tipo ?desc ?horario ?equipamiento ?transporte ?telefono ?email ?url ?accesibilidad
         ?streetType ?streetName ?streetNumber ?postalCode
         ?distritoUri ?distritoLabel ?wikidataDistrito
         ?barrioUri ?barrioLabel ?wikidataBarrio
"""


def load_text(name):
    for path in (ROOT / "vendor" / name, Path("/tmp") / name):
        if path.exists():
            return path.read_text(encoding="utf-8")
    raise SystemExit(f"No encuentro {name} en app/vendor/.")


def clean_uri_tail(val):
    if val is None:
        return None
    text = str(val).strip()
    if text.startswith("http://") or text.startswith("https://"):
        text = text.split("/")[-1]
    return urllib.parse.unquote(text).replace("_", " ")


def format_center_type(val):
    if val is None or str(val).strip() == "":
        return None
    raw = str(val).strip().split("/")[-1]
    return re.sub(r"(?<!^)(?=[A-ZÁÉÍÓÚÑ])", " ", raw) or None


def text(val):
    if val is None:
        return None
    out = str(val).strip()
    return out or None


def number(val):
    if val is None:
        return None
    try:
        return round(float(val), 6)
    except ValueError:
        return None


def put(row, key, value):
    if value is not None:
        row[key] = value


def centers_from(graph):
    seen = set()
    rows = []
    for row in graph.query(CENTERS_QUERY):
        uri = str(row.centro)
        if uri in seen:
            continue
        seen.add(uri)
        street_name = text(row.streetName)
        if street_name:
            parts = [text(row.streetType) or "", street_name]
            number_text = text(row.streetNumber)
            direccion = " ".join(part for part in parts if part).strip()
            if number_text:
                direccion = f"{direccion}, {number_text}"
        else:
            direccion = None
        item = {"uri": uri}
        put(item, "nombre", text(row.nombre))
        put(item, "tipo", format_center_type(row.tipo))
        put(item, "tipoRaw", text(row.tipo))
        put(item, "descripcion", text(row.desc))
        put(item, "distrito", text(row.distritoLabel) or clean_uri_tail(row.distritoUri))
        put(item, "wdDistrito", text(row.wikidataDistrito))
        put(item, "barrio", text(row.barrioLabel) or clean_uri_tail(row.barrioUri))
        put(item, "wdBarrio", text(row.wikidataBarrio))
        put(item, "direccion", direccion)
        put(item, "cp", text(row.postalCode))
        put(item, "telefono", text(row.telefono))
        put(item, "email", text(row.email))
        put(item, "transporte", text(row.transporte))
        put(item, "horario", text(row.horario))
        put(item, "equipamiento", text(row.equipamiento))
        put(item, "accesibilidad", text(row.accesibilidad))
        put(item, "web", text(row.url))
        put(item, "lat", number(row.lat))
        put(item, "lon", number(row.long))
        rows.append(item)
    return rows


def run_queries(graph):
    out = []
    for title, sparql in QUERIES:
        result = graph.query(sparql)
        variables = [str(var) for var in result.vars]
        table = []
        for row in result:
            table.append(["" if cell is None else str(cell) for cell in row])
        out.append({"title": title, "sparql": sparql.strip(), "vars": variables, "rows": table})
        print(f"  {title[:48]} -> {len(table)}")
    return out


def build_html(payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    css = load_text("leaflet.css")
    js = re.sub(r"//# sourceMappingURL=\S+", "", load_text("leaflet.min.js"))
    html = TEMPLATE.replace("@@LEAFLET_CSS@@", css).replace("@@LEAFLET_JS@@", js).replace("@@DATA@@", data)
    for token in ("@@LEAFLET_CSS@@", "@@LEAFLET_JS@@", "@@DATA@@"):
        if token in html:
            raise SystemExit(f"Quedó sin sustituir {token}")
    if "</script" in js.lower():
        raise SystemExit("Leaflet contiene un cierre de script y no se puede incrustar tal cual.")
    return html


def main():
    graph = Graph()
    print(f"Leyendo {RDF_PATH.name} ...")
    graph.parse(RDF_PATH, format="nt")
    print(f"Tripletas: {len(graph)}")
    centers = centers_from(graph)
    print(f"Centros: {len(centers)}")
    print(f"Con coordenadas: {sum(1 for c in centers if 'lat' in c and 'lon' in c)}")
    print("Consultas:")
    payload = {
        "triples": len(graph),
        "source": RDF_PATH.name,
        "centers": centers,
        "queries": run_queries(graph),
    }
    html = build_html(payload)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Escrito {OUT_PATH} ({OUT_PATH.stat().st_size:,} bytes)")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Educa Madrid — buscador y consultas</title>
<style>
@@LEAFLET_CSS@@
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body {
  margin: 0;
  padding: 20px 28px 48px;
  font-family: "Segoe UI", system-ui, sans-serif;
  color: #1c1917;
  background: #f6f3ef;
  line-height: 1.45;
}
header { border-bottom: 3px solid #9f1239; margin-bottom: 18px; padding-bottom: 12px; }
.kicker { margin: 0; color: #9f1239; font-size: 13px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }
h1 { font-size: 32px; line-height: 1.1; margin: 4px 0 8px; letter-spacing: -0.02em; }
h2 { font-size: 18px; margin: 0 0 8px; }
h3 { font-size: 20px; margin: 0 0 8px; }
#lead, .note, footer { color: #57534e; }
#lead { margin: 0; max-width: 78ch; }
.layout { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 18px; align-items: start; }
aside, .panel, .kpi { background: #fff; border: 1px solid #e7e5e4; border-radius: 12px; }
aside { padding: 16px; position: sticky; top: 12px; max-height: calc(100vh - 24px); overflow: auto; }
aside h2 { margin-bottom: 4px; }
label { display: block; font-size: 13px; font-weight: 650; margin: 10px 0 4px; }
select, input[type="search"] {
  width: 100%;
  padding: 7px 8px;
  border: 1px solid #d6d3d1;
  border-radius: 8px;
  background: #fff;
  font: inherit;
  color: inherit;
}
button, .tab, .modes button { font: inherit; cursor: pointer; }
button:focus-visible, select:focus-visible, input:focus-visible { outline: 2px solid #9f1239; outline-offset: 2px; }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.kpi { padding: 12px 14px; }
.kpi b { display: block; font-size: 28px; line-height: 1.1; color: #9f1239; font-variant-numeric: tabular-nums; }
.kpi span { color: #57534e; font-size: 13px; }
.tabs, .modes { display: flex; flex-wrap: wrap; gap: 8px; }
.tabs { margin: 16px 0; }
.tab, .modes button, .pager button {
  border: 1px solid #d6d3d1;
  background: #fff;
  color: #1c1917;
  border-radius: 999px;
  padding: 7px 12px;
}
.tab[aria-selected="true"], .modes button[aria-pressed="true"] { background: #9f1239; color: #fff; border-color: #9f1239; }
.panel { padding: 16px; }
.note { font-size: 14px; margin: 0 0 12px; }
.count { font-weight: 650; margin: 10px 0; }
pre {
  background: #1c1917;
  color: #f5f5f4;
  padding: 14px 16px;
  border-radius: 8px;
  overflow: auto;
  max-height: 240px;
  font-size: 12.5px;
  line-height: 1.45;
  margin: 0;
}
.table-wrap { overflow: auto; max-height: 480px; border: 1px solid #e7e5e4; border-radius: 8px; background: #fff; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 8px 10px; vertical-align: top; border-bottom: 1px solid #f5f5f4; }
th { position: sticky; top: 0; background: #fafaf9; font-size: 13px; }
tbody tr:nth-child(even) { background: #fafaf9; }
td { max-width: 380px; word-break: break-word; }
td a { word-break: break-all; }
a { color: #9f1239; }
.pager { display: flex; gap: 12px; align-items: center; margin-top: 10px; }
.pager button:disabled { opacity: 0.45; cursor: default; }
details { border-bottom: 1px solid #e7e5e4; }
summary { cursor: pointer; font-weight: 650; padding: 9px 0; }
.card { display: grid; grid-template-columns: 1fr 1fr; gap: 4px 28px; padding: 4px 0 12px; }
.card p { margin: 4px 0; }
.uri { grid-column: 1 / -1; color: #57534e; font-size: 12px; word-break: break-all; }
#map { height: 520px; border-radius: 10px; border: 1px solid #e7e5e4; background: #e7e5e4; }
.map-tools { margin: 12px 0; }
#map-detail { margin-top: 8px; }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }
.bar-row { display: grid; grid-template-columns: minmax(120px, 210px) minmax(0, 1fr) 52px; gap: 8px; align-items: center; margin: 5px 0; font-size: 13px; }
.bar-label { line-height: 1.25; }
.bar-track { background: #f5f5f4; height: 10px; border-radius: 99px; overflow: hidden; }
.bar-fill { background: #9f1239; height: 100%; border-radius: 99px; }
.bar-n { text-align: right; font-variant-numeric: tabular-nums; }
.empty { color: #57534e; }
footer { margin-top: 22px; font-size: 13px; }
@media (max-width: 980px) {
  body { padding: 16px; }
  .layout, .kpis, .stats, .card { grid-template-columns: 1fr; }
  aside { position: static; max-height: none; }
  .kpis { grid-template-columns: 1fr 1fr; }
}
</style>
</head>
<body>
<header>
  <p class="kicker">Web Semántica · Grupo 13</p>
  <h1>Educa Madrid</h1>
  <p id="lead"></p>
</header>
<div class="layout">
  <aside>
    <h2>Filtros</h2>
    <p class="note">Buscan en los centros del grafo. Afectan a las fichas, el mapa, las estadísticas y la consulta generada.</p>
    <label for="f-distrito">Distrito</label>
    <select id="f-distrito"></select>
    <label for="f-barrio">Barrio</label>
    <select id="f-barrio"></select>
    <label for="f-tipo">Tipología</label>
    <select id="f-tipo"></select>
    <label for="f-cp">Código postal</label>
    <select id="f-cp"></select>
    <label for="f-acc">Código de accesibilidad</label>
    <select id="f-acc"></select>
    <label for="f-nombre">Nombre del centro</label>
    <input id="f-nombre" type="search" placeholder="Parte del nombre" autocomplete="off">
    <label for="f-desc">Enseñanza o etapa</label>
    <input id="f-desc" type="search" placeholder="Infantil, ESO, bilingüe" autocomplete="off">
    <label for="f-equip">Equipamiento</label>
    <input id="f-equip" type="search" placeholder="Comedor, horario ampliado" autocomplete="off">
    <label for="f-transp">Transporte</label>
    <input id="f-transp" type="search" placeholder="Metro, Renfe, bus" autocomplete="off">
  </aside>
  <main>
    <section class="kpis" aria-label="Resumen">
      <div class="kpi"><b id="kpi-centers">0</b><span>Centros encontrados</span></div>
      <div class="kpi"><b id="kpi-distritos">0</b><span>Distritos</span></div>
      <div class="kpi"><b id="kpi-barrios">0</b><span>Barrios</span></div>
      <div class="kpi"><b id="kpi-tipos">0</b><span>Tipologías</span></div>
    </section>
    <div class="tabs" role="tablist">
      <button type="button" class="tab" id="tab-sparql" aria-selected="true">Consultas SPARQL</button>
      <button type="button" class="tab" id="tab-list">Fichas</button>
      <button type="button" class="tab" id="tab-map">Mapa</button>
      <button type="button" class="tab" id="tab-stats">Estadísticas</button>
    </div>
    <section class="panel" id="panel-sparql">
      <h2>Consultas SPARQL</h2>
      <div class="modes">
        <button type="button" id="mode-catalog" aria-pressed="true">Consultas preparadas</button>
        <button type="button" id="mode-filters" aria-pressed="false">Consulta de los filtros</button>
      </div>
      <div id="sparql-catalog">
        <label for="q-select">Pregunta</label>
        <select id="q-select"></select>
        <p class="note">Resultado calculado sobre el grafo local al generar este archivo. Desde aquí no se lanzan consultas nuevas.</p>
        <pre id="q-sparql"></pre>
        <p id="q-count" class="count"></p>
        <div id="q-table"></div>
      </div>
      <div id="sparql-filters" hidden>
        <p class="note">Esta consulta es la que corresponde a los filtros de la izquierda. La tabla son los centros del grafo que los cumplen.</p>
        <pre id="q-dyn"></pre>
        <p id="q-dyn-count" class="count"></p>
        <div id="q-dyn-table"></div>
      </div>
    </section>
    <section class="panel" id="panel-list" hidden>
      <h2 id="list-title">Fichas</h2>
      <p id="list-note" class="note"></p>
      <div id="list-host"></div>
    </section>
    <section class="panel" id="panel-map" hidden>
      <h2>Mapa</h2>
      <p id="map-caption" class="note"></p>
      <div id="map"></div>
      <div class="map-tools">
        <label for="map-select">Centro seleccionado</label>
        <select id="map-select"></select>
      </div>
      <div id="map-detail"></div>
    </section>
    <section class="panel" id="panel-stats" hidden>
      <h2>Estadísticas del filtro actual</h2>
      <div class="stats">
        <div>
          <h3>Centros por distrito</h3>
          <div id="stat-distrito"></div>
        </div>
        <div>
          <h3>Centros por código de accesibilidad</h3>
          <div id="stat-acc"></div>
        </div>
      </div>
    </section>
  </main>
</div>
<footer>
  <p>Fuente: Portal de Datos Abiertos del Ayuntamiento de Madrid, licencia CC BY 4.0. Los enlaces de distrito y barrio abren la entidad correspondiente en Wikidata. El plano del mapa procede de OpenStreetMap.</p>
</footer>
<script>
@@LEAFLET_JS@@
</script>
<script id="edu-data" type="application/json">
@@DATA@@
</script>
<script>
const DATA = JSON.parse(document.getElementById("edu-data").textContent);
const PAGE = 25;
const LABELS = {
  distrito: "Distrito",
  totalCentros: "Centros",
  wikidataDistrito: "Wikidata del distrito",
  barrio: "Barrio",
  wikidataBarrio: "Wikidata del barrio",
  codigoAccesibilidad: "Código de accesibilidad",
  nombre: "Nombre",
  telefono: "Teléfono",
  email: "Email",
  equipamiento: "Equipamiento",
  descripcion: "Descripción",
  transporte: "Transporte",
  tipo: "Tipo",
  centro: "Centro",
  pk: "Identificador",
  cp: "Código postal",
  accesibilidad: "Accesibilidad"
};
const filters = {
  distrito: "Todos",
  barrio: "Todos",
  tipo: "Todos",
  cp: "Todos",
  acc: "Todos",
  nombre: "",
  desc: "",
  equip: "",
  transp: ""
};
let catalogPage = 0;
let dynPage = 0;
let lastKey = "";
let currentRows = DATA.centers;
let selectedUri = null;
let map = null;
let layer = null;
let mapReady = false;
const markers = new Map();

function $(id) { return document.getElementById(id); }
function formatNumber(value) { return Number(value).toLocaleString("es-ES"); }
function countCentros(value) {
  return formatNumber(value) + (Number(value) === 1 ? " centro" : " centros");
}

function uniqSorted(values, numeric) {
  const clean = values.filter(value => value != null && String(value).trim() !== "");
  return [...new Set(clean)].sort((a, b) => String(a).localeCompare(String(b), "es", { numeric: !!numeric, sensitivity: "base" }));
}

function fillSelect(select, values, current) {
  const next = ["Todos", ...values];
  select.replaceChildren();
  for (const value of next) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  }
  select.value = next.includes(current) ? current : "Todos";
}

function refillBarrio() {
  const distrito = $("f-distrito").value || "Todos";
  const source = distrito === "Todos" ? DATA.centers : DATA.centers.filter(center => center.distrito === distrito);
  const values = uniqSorted(source.map(center => center.barrio));
  const current = $("f-barrio").value;
  fillSelect($("f-barrio"), values, values.includes(current) ? current : "Todos");
}

function readFilters() {
  filters.distrito = $("f-distrito").value || "Todos";
  filters.barrio = $("f-barrio").value || "Todos";
  filters.tipo = $("f-tipo").value || "Todos";
  filters.cp = $("f-cp").value || "Todos";
  filters.acc = $("f-acc").value || "Todos";
  filters.nombre = $("f-nombre").value.trim();
  filters.desc = $("f-desc").value.trim();
  filters.equip = $("f-equip").value.trim();
  filters.transp = $("f-transp").value.trim();
}

function contains(value, query) {
  if (!query) return true;
  if (!value) return false;
  return String(value).toLowerCase().includes(query.toLowerCase());
}

function applyFilters() {
  return DATA.centers.filter(center => {
    if (filters.distrito !== "Todos" && center.distrito !== filters.distrito) return false;
    if (filters.barrio !== "Todos" && center.barrio !== filters.barrio) return false;
    if (filters.tipo !== "Todos" && center.tipo !== filters.tipo) return false;
    if (filters.cp !== "Todos" && center.cp !== filters.cp) return false;
    if (filters.acc !== "Todos" && center.accesibilidad !== filters.acc) return false;
    if (!contains(center.nombre, filters.nombre)) return false;
    if (!contains(center.descripcion, filters.desc)) return false;
    if (!contains(center.equipamiento, filters.equip)) return false;
    if (!contains(center.transporte, filters.transp)) return false;
    return true;
  });
}

function sparqlString(value) {
  return '"' + String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
}

function buildSparql() {
  const lines = [];
  if (filters.distrito !== "Todos") lines.push("FILTER(?distrito = " + sparqlString(filters.distrito) + ")");
  if (filters.barrio !== "Todos") lines.push("FILTER(?barrio = " + sparqlString(filters.barrio) + ")");
  if (filters.tipo !== "Todos") {
    const raws = [...new Set(DATA.centers.filter(center => center.tipo === filters.tipo && center.tipoRaw).map(center => center.tipoRaw))];
    if (raws.length === 1) lines.push("FILTER(?tipo = " + sparqlString(raws[0]) + ")");
    else if (raws.length > 1) lines.push("FILTER(?tipo IN (" + raws.map(sparqlString).join(", ") + "))");
  }
  if (filters.cp !== "Todos") lines.push("FILTER(?cp = " + sparqlString(filters.cp) + ")");
  if (filters.acc !== "Todos") lines.push("FILTER(?accesibilidad = " + sparqlString(filters.acc) + ")");
  if (filters.nombre) lines.push("FILTER(CONTAINS(LCASE(?nombre), " + sparqlString(filters.nombre.toLowerCase()) + "))");
  if (filters.desc) lines.push("FILTER(BOUND(?descripcion) && CONTAINS(LCASE(?descripcion), " + sparqlString(filters.desc.toLowerCase()) + "))");
  if (filters.equip) lines.push("FILTER(BOUND(?equipamiento) && CONTAINS(LCASE(?equipamiento), " + sparqlString(filters.equip.toLowerCase()) + "))");
  if (filters.transp) lines.push("FILTER(BOUND(?transporte) && CONTAINS(LCASE(?transporte), " + sparqlString(filters.transp.toLowerCase()) + "))");
  const block = lines.map(line => "    " + line).join("\n");
  return [
    "PREFIX ont: <http://educamadrid.linkeddata.es/ontology/CentroEducativo#>",
    "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>",
    "PREFIX owl: <http://www.w3.org/2002/07/owl#>",
    "",
    "SELECT DISTINCT ?nombre ?distrito ?barrio ?cp ?accesibilidad ?telefono ?email",
    "WHERE {",
    "    ?centro a ont:EducationalCenter ;",
    "            ont:centerName ?nombre ;",
    "            ont:hasAddress ?addr .",
    "    ?addr ont:inDistrict ?distUri ;",
    "          ont:inNeighborhood ?barrioUri .",
    "    ?distUri rdfs:label ?distrito .",
    "    ?barrioUri rdfs:label ?barrio .",
    "    OPTIONAL { ?addr ont:postalCode ?cp . }",
    "    OPTIONAL { ?centro ont:centerType ?tipo . }",
    "    OPTIONAL { ?centro ont:accessibilityCode ?accesibilidad . }",
    "    OPTIONAL { ?centro ont:description ?descripcion . }",
    "    OPTIONAL { ?centro ont:equipment ?equipamiento . }",
    "    OPTIONAL { ?centro ont:transportation ?transporte . }",
    "    OPTIONAL { ?centro ont:telephone ?telefono . }",
    "    OPTIONAL { ?centro ont:email ?email . }",
    block,
    "}",
    "ORDER BY ?distrito ?nombre"
  ].filter(line => line !== "").join("\n");
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
}

function addField(parent, label, value) {
  if (value == null || value === "") return;
  const p = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = label + ": ";
  p.append(strong, document.createTextNode(value));
  parent.appendChild(p);
}

function addLinkField(parent, label, value, href) {
  if (!value) return;
  const p = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = label + ": ";
  p.appendChild(strong);
  if (href) {
    const a = document.createElement("a");
    a.href = href;
    a.textContent = value;
    if (/^https?:/i.test(href)) {
      a.target = "_blank";
      a.rel = "noopener";
    }
    p.appendChild(a);
  } else {
    p.appendChild(document.createTextNode(value));
  }
  parent.appendChild(p);
}

function addPlace(parent, center) {
  if (!center.distrito && !center.barrio) return;
  const p = document.createElement("p");
  const strong = document.createElement("strong");
  strong.textContent = "Distrito: ";
  p.appendChild(strong);
  appendMaybeLink(p, center.distrito || "—", center.wdDistrito);
  p.appendChild(document.createTextNode(" · Barrio: "));
  appendMaybeLink(p, center.barrio || "—", center.wdBarrio);
  parent.appendChild(p);
}

function appendMaybeLink(parent, text, href) {
  if (href && /^https?:\/\//i.test(href)) {
    const a = document.createElement("a");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = text;
    parent.appendChild(a);
  } else {
    parent.appendChild(document.createTextNode(text));
  }
}

function buildCard(center) {
  const card = document.createElement("div");
  card.className = "card";
  const left = document.createElement("div");
  const right = document.createElement("div");
  if (center.direccion || center.cp) {
    const dir = [center.direccion, center.cp ? "CP " + center.cp : ""].filter(Boolean).join(" · ");
    addField(left, "Dirección", dir);
  }
  addPlace(left, center);
  addField(left, "Descripción", center.descripcion);
  addField(left, "Equipamiento", center.equipamiento);
  addField(right, "Transporte", center.transporte);
  addField(right, "Accesibilidad", center.accesibilidad);
  addField(right, "Horario", center.horario);
  addLinkField(right, "Teléfono", center.telefono, center.telefono ? "tel:" + String(center.telefono).replace(/[^\d+]/g, "") : "");
  addLinkField(right, "Email", center.email, center.email ? "mailto:" + center.email : "");
  addLinkField(right, "Ficha oficial", center.web ? "Ver en el portal de Madrid" : "", center.web);
  card.append(left, right);
  if (center.uri) {
    const uri = document.createElement("p");
    uri.className = "uri";
    uri.textContent = "URI: " + center.uri;
    card.appendChild(uri);
  }
  return card;
}

function renderTable(container, columns, rows, page, setPage) {
  container.replaceChildren();
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const safePage = Math.min(Math.max(page, 0), pages - 1);
  const slice = rows.slice(safePage * PAGE, safePage * PAGE + PAGE);
  const table = document.createElement("table");
  const head = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = LABELS[column] || column;
    head.appendChild(th);
  }
  const thead = document.createElement("thead");
  thead.appendChild(head);
  const tbody = document.createElement("tbody");
  for (const row of slice) {
    const tr = document.createElement("tr");
    row.forEach(cell => {
      const td = document.createElement("td");
      const text = cell == null ? "" : String(cell);
      if (/^https?:\/\//i.test(text)) {
        const a = document.createElement("a");
        a.href = text;
        a.target = "_blank";
        a.rel = "noopener";
        a.textContent = text.replace(/^https?:\/\/(www\.)?/, "");
        td.appendChild(a);
      } else {
        td.textContent = text;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  }
  table.append(thead, tbody);
  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  wrap.appendChild(table);
  container.appendChild(wrap);
  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Esta consulta no devuelve filas.";
    container.appendChild(empty);
  }
  if (rows.length > PAGE) {
    const pager = document.createElement("div");
    pager.className = "pager";
    const info = document.createElement("span");
    info.textContent = "Filas " + formatNumber(safePage * PAGE + 1) + "–" + formatNumber(Math.min(rows.length, safePage * PAGE + PAGE)) + " de " + formatNumber(rows.length);
    const prev = document.createElement("button");
    prev.type = "button";
    prev.textContent = "Anterior";
    prev.disabled = safePage === 0;
    prev.addEventListener("click", () => setPage(safePage - 1));
    const next = document.createElement("button");
    next.type = "button";
    next.textContent = "Siguiente";
    next.disabled = safePage >= pages - 1;
    next.addEventListener("click", () => setPage(safePage + 1));
    pager.append(prev, info, next);
    container.appendChild(pager);
  }
}

function renderCatalog() {
  const query = DATA.queries[Number($("q-select").value) || 0];
  $("q-sparql").textContent = query.sparql;
  $("q-count").textContent = formatNumber(query.rows.length) + " resultados";
  const pages = Math.max(1, Math.ceil(query.rows.length / PAGE));
  if (catalogPage > pages - 1) catalogPage = pages - 1;
  renderTable($("q-table"), query.vars, query.rows, catalogPage, page => {
    catalogPage = page;
    renderCatalog();
  });
}

function renderDynamic(rows) {
  const sorted = rows.slice().sort((a, b) =>
    (a.distrito || "").localeCompare(b.distrito || "", "es") ||
    (a.nombre || "").localeCompare(b.nombre || "", "es")
  );
  const tableRows = sorted.map(center => [
    center.nombre || "",
    center.distrito || "",
    center.barrio || "",
    center.cp || "",
    center.accesibilidad || "",
    center.telefono || "",
    center.email || ""
  ]);
  $("q-dyn").textContent = buildSparql();
  $("q-dyn-count").textContent = countCentros(tableRows.length) + (tableRows.length === 1 ? " cumple los filtros" : " cumplen los filtros");
  const pages = Math.max(1, Math.ceil(tableRows.length / PAGE));
  if (dynPage > pages - 1) dynPage = 0;
  renderTable($("q-dyn-table"), ["nombre", "distrito", "barrio", "cp", "accesibilidad", "telefono", "email"], tableRows, dynPage, page => {
    dynPage = page;
    renderDynamic(currentRows);
  });
}

function renderList(rows) {
  $("list-title").textContent = "Fichas (" + formatNumber(rows.length) + ")";
  const host = $("list-host");
  host.replaceChildren();
  if (!rows.length) {
    $("list-note").textContent = "Ningún centro cumple todos los filtros.";
    return;
  }
  const ordered = rows.slice().sort((a, b) => (a.nombre || "").localeCompare(b.nombre || "", "es"));
  const shown = ordered.slice(0, 100);
  $("list-note").textContent = rows.length > 100
    ? "Mostrando las primeras 100 fichas, ordenadas por nombre. Acota con los filtros para ver el resto."
    : "Ordenadas por nombre.";
  for (const center of shown) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = center.nombre + (center.tipo ? " — " + center.tipo : "");
    details.append(summary, buildCard(center));
    host.appendChild(details);
  }
}

function counts(rows, key) {
  const map = new Map();
  for (const row of rows) {
    const label = row[key];
    if (label == null || label === "") continue;
    map.set(label, (map.get(label) || 0) + 1);
  }
  return [...map.entries()]
    .map(([label, n]) => ({ label, n }))
    .sort((a, b) => b.n - a.n || String(a.label).localeCompare(String(b.label), "es", { numeric: true }));
}

function renderBars(container, pairs) {
  container.replaceChildren();
  if (!pairs.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "No hay datos para este filtro.";
    container.appendChild(empty);
    return;
  }
  const max = Math.max(...pairs.map(item => item.n));
  for (const item of pairs) {
    const row = document.createElement("div");
    row.className = "bar-row";
    const label = document.createElement("span");
    label.className = "bar-label";
    label.textContent = item.label;
    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = (item.n / max * 100) + "%";
    track.appendChild(fill);
    const n = document.createElement("span");
    n.className = "bar-n";
    n.textContent = formatNumber(item.n);
    row.append(label, track, n);
    container.appendChild(row);
  }
}

function renderStats(rows) {
  renderBars($("stat-distrito"), counts(rows, "distrito"));
  renderBars($("stat-acc"), counts(rows, "accesibilidad"));
}

function renderKpis(rows) {
  const unique = key => new Set(rows.map(row => row[key]).filter(value => value != null && value !== "")).size;
  $("kpi-centers").textContent = formatNumber(rows.length);
  $("kpi-distritos").textContent = formatNumber(unique("distrito"));
  $("kpi-barrios").textContent = formatNumber(unique("barrio"));
  $("kpi-tipos").textContent = formatNumber(unique("tipo"));
}

function hasCoord(center) {
  return typeof center.lat === "number" && typeof center.lon === "number";
}

function popupHtml(center) {
  return [
    "<strong>" + esc(center.nombre || "Centro") + "</strong>",
    center.tipo ? esc(center.tipo) : "",
    center.direccion ? esc(center.direccion) : "",
    [center.distrito, center.barrio].filter(Boolean).map(esc).join(" · "),
    center.telefono ? "Tel. " + esc(center.telefono) : "",
    center.accesibilidad ? "Accesibilidad " + esc(center.accesibilidad) : ""
  ].filter(Boolean).join("<br>");
}

function styleFor(center) {
  const selected = center.uri === selectedUri;
  return {
    radius: selected ? 11 : 7,
    color: selected ? "#1c1917" : "#9f1239",
    weight: selected ? 2 : 1,
    fillColor: "#e11d48",
    fillOpacity: 0.9
  };
}

function highlightSelected() {
  markers.forEach((marker, uri) => {
    const center = currentRows.find(item => item.uri === uri);
    if (center) marker.setStyle(styleFor(center));
  });
}

function renderMapDetail(points) {
  const host = $("map-detail");
  host.replaceChildren();
  const center = points.find(item => item.uri === selectedUri);
  if (!center) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Elige un centro en el mapa o en la lista.";
    host.appendChild(empty);
    return;
  }
  const title = document.createElement("h3");
  title.textContent = center.nombre || "Centro";
  host.append(title, buildCard(center));
}

function fillMapSelect(points) {
  const select = $("map-select");
  select.replaceChildren();
  for (const center of points) {
    const option = document.createElement("option");
    option.value = center.uri;
    option.textContent = (center.nombre || "Centro") + " (" + (center.distrito || "—") + " · " + (center.barrio || "—") + ")";
    select.appendChild(option);
  }
  select.disabled = points.length === 0;
  if (selectedUri) select.value = selectedUri;
}

function renderMap(rows) {
  if (!mapReady) return;
  layer.clearLayers();
  markers.clear();
  const points = rows.filter(hasCoord);
  $("map-caption").textContent = points.length
    ? "Mostrando " + countCentros(points.length) + " con coordenadas. El plano se descarga de OpenStreetMap."
    : "Ninguno de los centros filtrados tiene coordenadas.";
  if (!points.some(center => center.uri === selectedUri)) selectedUri = points[0] ? points[0].uri : null;
  fillMapSelect(points);
  const bounds = [];
  for (const center of points) {
    const marker = L.circleMarker([center.lat, center.lon], styleFor(center));
    marker.bindPopup(popupHtml(center));
    marker.on("click", () => selectCenter(center.uri, false));
    marker.addTo(layer);
    markers.set(center.uri, marker);
    bounds.push([center.lat, center.lon]);
  }
  if (bounds.length === 1) map.setView(bounds[0], 15);
  else if (bounds.length > 1) map.fitBounds(bounds, { padding: [28, 28], maxZoom: 14 });
  else map.setView([40.4168, -3.7038], 11);
  renderMapDetail(points);
}

function selectCenter(uri, pan) {
  selectedUri = uri;
  if ($("map-select").value !== uri) $("map-select").value = uri;
  highlightSelected();
  renderMapDetail(currentRows.filter(hasCoord));
  const marker = markers.get(uri);
  if (pan && marker) {
    map.panTo(marker.getLatLng());
    marker.openPopup();
  }
}

function ensureMap() {
  if (!mapReady) {
    map = L.map("map", { preferCanvas: true }).setView([40.4168, -3.7038], 11);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);
    layer = L.layerGroup().addTo(map);
    mapReady = true;
  }
  setTimeout(() => {
    map.invalidateSize();
    renderMap(currentRows);
  }, 60);
}

function showTab(name) {
  for (const id of ["sparql", "list", "map", "stats"]) {
    $("panel-" + id).hidden = id !== name;
    $("tab-" + id).setAttribute("aria-selected", id === name ? "true" : "false");
  }
  if (name === "map") ensureMap();
}

function setMode(mode) {
  $("sparql-catalog").hidden = mode !== "catalog";
  $("sparql-filters").hidden = mode !== "filters";
  $("mode-catalog").setAttribute("aria-pressed", mode === "catalog" ? "true" : "false");
  $("mode-filters").setAttribute("aria-pressed", mode === "filters" ? "true" : "false");
}

function update() {
  readFilters();
  const key = JSON.stringify(filters);
  if (key !== lastKey) {
    lastKey = key;
    dynPage = 0;
  }
  const rows = applyFilters();
  currentRows = rows;
  renderKpis(rows);
  renderDynamic(rows);
  renderList(rows);
  renderStats(rows);
  if (mapReady) renderMap(rows);
}

function init() {
  $("lead").textContent = "Buscador de los " + formatNumber(DATA.centers.length) + " centros educativos de Madrid. Los datos y las respuestas SPARQL van dentro de este archivo (" + formatNumber(DATA.triples) + " tripletas). El plano del mapa necesita internet; el resto, no.";
  fillSelect($("f-distrito"), uniqSorted(DATA.centers.map(center => center.distrito)), "Todos");
  fillSelect($("f-tipo"), uniqSorted(DATA.centers.map(center => center.tipo)), "Todos");
  fillSelect($("f-cp"), uniqSorted(DATA.centers.map(center => center.cp), true), "Todos");
  fillSelect($("f-acc"), uniqSorted(DATA.centers.map(center => center.accesibilidad), true), "Todos");
  refillBarrio();
  for (const [index, query] of DATA.queries.entries()) {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = query.title;
    $("q-select").appendChild(option);
  }
  $("q-select").addEventListener("change", () => {
    catalogPage = 0;
    renderCatalog();
  });
  for (const id of ["f-distrito", "f-barrio", "f-tipo", "f-cp", "f-acc"]) {
    $(id).addEventListener("change", () => {
      if (id === "f-distrito") refillBarrio();
      update();
    });
  }
  for (const id of ["f-nombre", "f-desc", "f-equip", "f-transp"]) {
    $(id).addEventListener("input", update);
  }
  $("tab-sparql").addEventListener("click", () => showTab("sparql"));
  $("tab-list").addEventListener("click", () => showTab("list"));
  $("tab-map").addEventListener("click", () => showTab("map"));
  $("tab-stats").addEventListener("click", () => showTab("stats"));
  $("mode-catalog").addEventListener("click", () => setMode("catalog"));
  $("mode-filters").addEventListener("click", () => setMode("filters"));
  $("map-select").addEventListener("change", () => {
    if ($("map-select").value) selectCenter($("map-select").value, true);
  });
  renderCatalog();
  setMode("catalog");
  showTab("sparql");
  update();
}

init();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
