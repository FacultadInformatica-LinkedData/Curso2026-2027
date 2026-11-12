"""Grafo RDF del grupo cargado en Oxigraph y consultas SPARQL con nombre.

El grafo y la ontología son copias de la entrega del grupo, en `graph/` (origen en el README).
Cada consulta vive en `queries/<nombre>.rq`. Los parámetros se escriben como `$nombre` y se
sustituyen por el término RDF serializado (IRI o literal escapado) antes de ejecutar.

Una línea `#include <fragmento>` se sustituye por el texto de `queries/<fragmento>.rq`, con la
misma sangría. Los fragmentos empiezan por `_` y no son consultas por sí solos: `_station.rq` es
el patrón común de estación (y la regla de estación utilizable) y necesita los prefijos `bm:`,
`geo:` y `rdfs:` en la consulta que lo incluye.
"""

import re
from functools import cache
from pathlib import Path
from string import Template
from textwrap import indent

import pyoxigraph as ox

from . import trace

ROOT = Path(__file__).resolve().parent.parent
GRAPH_DIR = ROOT / "graph"
QUERIES = Path(__file__).parent / "queries"

STREET = "https://bicismart.madrid.data.es/resource/Street/"
XSD = "http://www.w3.org/2001/XMLSchema#"


def _load_store() -> ox.Store:
    store = ox.Store()
    store.load(path=GRAPH_DIR / "bicimad-with-links-updated.ttl", format=ox.RdfFormat.TURTLE)
    store.load(path=GRAPH_DIR / "bicismart-ontology-updated.ttl", format=ox.RdfFormat.TURTLE)
    return store


store = _load_store()


_INCLUDE = re.compile(r"^([ \t]*)#include (\w+)[ \t]*$", re.MULTILINE)


def _source(name: str) -> str:
    """Texto de `queries/<name>.rq` con los `#include` ya sustituidos."""
    text = (QUERIES / f"{name}.rq").read_text(encoding="utf-8")
    return _INCLUDE.sub(lambda match: indent(_source(match[2]).rstrip("\n"), match[1]), text)


@cache
def _template(name: str) -> Template:
    return Template(_source(name))


def _term(value) -> str:
    """Parámetro de una consulta -> término SPARQL serializado: un IRI o un literal tal cual, y
    cualquier otro valor convertido en literal (un texto, escapado).
    """
    if isinstance(value, ox.NamedNode | ox.Literal):
        return str(value)
    return str(ox.Literal(value))


def _python(term):
    """Término de un resultado -> valor Python: int, float o bool según su tipo XSD y, si no,
    su texto (también los IRI). Una variable sin valor da None.
    """
    if term is None:
        return None
    if isinstance(term, ox.Literal):
        datatype = term.datatype.value
        if datatype == XSD + "integer":
            return int(term.value)
        if datatype in (XSD + "double", XSD + "decimal", XSD + "float"):
            return float(term.value)
        if datatype == XSD + "boolean":
            return term.value == "true"
    return term.value


def _text(name: str, params: dict) -> str:
    return _template(name).substitute({key: _term(value) for key, value in params.items()})


def _run(name: str, text: str, note: str | None = None) -> list[dict]:
    with trace.record("local", name, text, note=note) as entry:
        result = store.query(text)
        names = [variable.value for variable in result.variables]
        rows = [
            dict(zip(names, (_python(solution[n]) for n in names), strict=True))
            for solution in result
        ]
        entry["rows"] = len(rows)
    return rows


def query(name: str, *, note: str | None = None, **params) -> list[dict]:
    """Ejecuta `queries/<name>.rq` y devuelve las filas como diccionarios de valores Python.

    `note` es un comentario para el panel sobre qué se hace con las filas (ver `trace.record`).
    """
    return _run(name, _text(name, params), note)


_results: dict[str, list[dict]] = {}


def query_cached(name: str, *, note: str | None = None, **params) -> list[dict]:
    """Como `query`, pero solo ejecuta la consulta la primera vez y después reutiliza las filas.

    El grafo no cambia mientras corre la app, así que el resultado vale para siempre. Cada llamada
    queda en el registro de la petición: como ejecutada la primera vez y como «en caché» las
    siguientes. Las filas se comparten entre llamadas: no hay que modificarlas.
    """
    text = _text(name, params)
    if text not in _results:
        _results[text] = _run(name, text, note)
        return _results[text]
    rows = _results[text]
    with trace.record("local", name, text, cached=True, note=note) as entry:
        entry["rows"] = len(rows)
    return rows


def street(key: str) -> ox.NamedNode:
    """'Calle_BravoMurillo' -> IRI de la calle."""
    return ox.NamedNode(STREET + key)


def street_key(iri: str) -> str:
    """IRI de la calle -> 'Calle_BravoMurillo', la referencia que usa la web."""
    return iri.removeprefix(STREET)
