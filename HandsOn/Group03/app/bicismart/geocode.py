"""Del texto que escribe el usuario a un origen o un destino.

Un destino puede ser una calle del Callejero (el número se ignora: el grafo modela calles, no
portales), un lugar de Wikidata, una estación BiciMAD o un punto del mapa. Las referencias que
viajan entre la web y la API tienen la forma `street:<calle>` (nombre de su IRI, p. ej.
`street:Calle_BravoMurillo`), `place:<QID>`, `station:<id>` o `pt:<lat>,<lon>`.
"""

import re
from dataclasses import dataclass

from . import geo, graph, wikidata
from .errors import BadRequest, NotFound
from .names import district_names, fold, pretty

STREET_TYPES = {
    "C", "CL", "CALLE", "AV", "AVD", "AVDA", "AVENIDA", "P", "PS", "PASEO", "PL", "PZA", "PLAZA",
    "GTA", "GLORIETA", "RONDA", "CAMINO", "CTRA", "CARRETERA", "TRAVESIA", "CUESTA",
    "COSTANILLA", "PASAJE", "CALLEJON", "BULEVAR", "VIA", "PLAZUELA",
}
PARTICLES = {"DE", "DEL", "LA", "LAS", "LOS", "EL"}
CATEGORY_ALIASES = {
    "estacion de metro": "metro", "estacion de tren": "estacion", "tren": "estacion",
}


@dataclass
class Endpoint:
    """Origen o destino ya situado."""

    label: str
    lat: float
    lon: float
    source: str  # de dónde sale la ubicación: user, bicimad, callejero o wikidata
    note: str  # cómo se ha resuelto, para enseñarlo al usuario
    # Qué se podría hacer solo con el CSV de BiciMAD, para el panel «¿Por qué ontología?»:
    # {"verdict": "yes" | "partial" | "no", "text": …}.
    csv: dict | None = None
    stations: list[dict] | None = None  # estaciones a las que se llega sin tramo a pie
    approximate: bool = False


def all_stations() -> list[dict]:
    """Todas las estaciones del grafo (consulta `stations`), ejecutada una sola vez por proceso."""
    return graph.query_cached("stations")


def parse_street(text: str) -> tuple[str, str | None]:
    """'Calle de Bravo Murillo, 120' -> ('BRAVO MURILLO', '120')."""
    words = re.sub(r"[,.ºª/]", " ", fold(text)).split()
    number = None
    if len(words) > 1 and re.fullmatch(r"\d+[A-Z]?", words[-1]):
        number = words.pop()
        if len(words) > 1 and words[-1] in ("N", "NO", "NUM", "NUMERO"):
            words.pop()
    if len(words) > 1 and words[0] in STREET_TYPES:
        words.pop(0)
    while len(words) > 1 and words[0] in PARTICLES:
        words.pop(0)
    return " ".join(words), number


def category_key(text: str) -> str | None:
    """'un museo', 'museos', 'Estación de metro' -> clave de wikidata.CATEGORIES."""
    words = fold(text).lower()
    words = re.sub(r"^(un|una|el|la|los|las|unos|unas)\s+", "", words)
    for candidate in (words, words.removesuffix("s"), words.removesuffix("es")):
        candidate = CATEGORY_ALIASES.get(candidate, candidate)
        if candidate in wikidata.CATEGORIES:
            return candidate
    return None


def _stations_label(count: int) -> str:
    return f"{count} estación" if count == 1 else f"{count} estaciones"


def _distance_label(meters: float) -> str:
    if meters >= 1000:
        return f"{meters / 1000:.1f} km".replace(".", ",")
    return f"{round(meters / 10) * 10:.0f} m"


def _category_results(key: str, near: tuple[float, float] | None) -> list[dict]:
    label = wikidata.CATEGORIES[key].label
    lat, lon = near or wikidata.CENTER
    places = [p for p in wikidata.places() if key in p["categories"]]
    wikidata.record_cached_places(key, len(places))
    where = "de tu origen" if near else "de Sol"
    return [
        {
            "kind": "place",
            "ref": f"place:{p['qid']}",
            "label": p["label"],
            "detail": f"{label} · a {_distance_label(meters)} {where}",
            "source": "wikidata",
        }
        for meters, p in geo.by_distance(places, lat, lon, k=5)
    ]


def _street_results(name: str, number: str | None) -> list[dict]:
    rows = graph.query("search_streets", text=name)

    def rank(row):
        if row["name"] == name:
            position = 0
        elif row["name"].startswith(name):
            position = 1
        elif re.search(rf"\b{re.escape(name)}\b", row["name"]):
            position = 2
        else:
            position = 3
        return (position, -row["stations"], len(row["name"]))

    results = []
    for row in sorted(rows, key=rank)[:6]:
        stations = row["stations"]
        parts = [district_names(row["districts"]) or "Sin distrito"]
        parts.append(_stations_label(stations) if stations else "sin estaciones")
        if row["wikidata"]:
            parts.append("Wikidata")
        if number:
            parts.append(f"nº {number} → toda la calle")
        results.append({
            "kind": "street",
            "ref": f"street:{graph.street_key(row['street'])}",
            "label": pretty(row["name"]),
            "detail": " · ".join(parts),
            "source": "callejero",
        })
    return results


def _place_results(text: str) -> list[dict]:
    needle = fold(text)
    found = [p for p in wikidata.places() if needle in fold(p["label"])]
    found.sort(key=lambda p: (not fold(p["label"]).startswith(needle), len(p["label"])))
    return [
        {
            "kind": "place",
            "ref": f"place:{p['qid']}",
            "label": p["label"],
            "detail": " · ".join(
                [", ".join(wikidata.CATEGORIES[c].label for c in p["categories"])]
                + ([p["description"]] if p.get("description") else [])
            ),
            "source": "wikidata",
        }
        for p in found[:5]
    ]


def _station_results(text: str) -> list[dict]:
    needle = fold(text)
    found = [s for s in all_stations() if needle in fold(s["name"])]
    return [
        {
            "kind": "station",
            "ref": f"station:{s['id']}",
            "label": s["name"],
            "detail": f"Estación BiciMAD · {s['capacity']} bases"
            + ("" if s["usable"] else " · fuera de servicio"),
            "source": "bicimad",
        }
        for s in found[:4]
    ]


def search(text: str, near: tuple[float, float] | None = None) -> list[dict]:
    """Sugerencias para lo que escribe el usuario, en este orden: lugares del tipo pedido (si el
    texto es un tipo, como «un museo»), calles del Callejero, lugares de Wikidata por nombre y
    estaciones BiciMAD.

    Cada sugerencia es {kind, ref, label, detail, source} y su `ref` se pasa después a `resolve`.
    `near` es el origen ya elegido, (lat, lon): los lugares de un tipo se ordenan por distancia a
    él o, si no hay, a la Puerta del Sol. Con menos de 2 caracteres no se busca nada.
    """
    text = text.strip()
    if len(text) < 2:
        return []
    results = []
    if key := category_key(text):
        results += _category_results(key, near)
    name, number = parse_street(text)
    if len(name) >= 3:
        results += _street_results(name, number)
    if len(text) >= 3:
        results += _place_results(text)
        results += _station_results(text)
    return results


def _street(key: str) -> Endpoint:
    node = graph.street(key)
    rows = graph.query("street", street=node)
    if not rows:
        raise NotFound(f"No existe la calle {key} en el Callejero.")
    info = rows[0]
    name = pretty(info["name"])

    stations = graph.query("street_stations", street=node)
    if stations:
        lat, lon = geo.centroid(stations)
        return Endpoint(
            name, lat, lon, "callejero",
            f"La calle tiene {_stations_label(len(stations))} BiciMAD (bm:locatedOnStreet): "
            "el trayecto empieza o termina en una de ellas, sin tramo a pie.",
            csv={"verdict": "partial", "text": (
                "Parcial: se podría buscar el texto en la dirección de las estaciones, pero sin "
                "identificar la calle (homónimos, abreviaturas) ni situar calles sin estación."
            )},
            stations=stations,
        )

    facts = wikidata.street_facts(wikidata.qid(info["wikidata"])) if info["wikidata"] else None
    if facts and "lat" in facts:
        return Endpoint(
            name, facts["lat"], facts["lon"], "wikidata",
            "La calle no tiene estaciones; se usan sus coordenadas en Wikidata "
            "(owl:sameAs → P625).",
            csv={"verdict": "no", "text": (
                "No: el CSV de BiciMAD no sabe dónde está una calle sin estaciones."
            )},
        )

    nearby = graph.query("neighborhood_stations", street=node)
    if nearby:
        lat, lon = geo.centroid(nearby)
        return Endpoint(
            name, lat, lon, "callejero",
            "La calle no tiene estaciones ni coordenadas en Wikidata; se sitúa de forma aproximada "
            "en el centro de las estaciones de su distrito y barrio (bm:districtCode, "
            "bm:neighborhoodCode).",
            csv={"verdict": "no", "text": "No: el CSV de BiciMAD no tiene distritos ni barrios."},
            approximate=True,
        )
    raise NotFound(f"No se ha podido situar la calle {name}.")


def resolve(ref: str, label: str | None = None) -> Endpoint:
    """Sitúa una referencia de la web. Lanza NotFound si no existe y BadRequest si no es válida.

    `ref` tiene una de las formas del principio del módulo (`street:`, `place:`, `station:` o
    `pt:`). `label` solo se usa para un punto del mapa, que no tiene nombre propio; los demás
    toman el suyo del grafo o de Wikidata.
    """
    kind, _, value = ref.partition(":")
    if kind == "pt":
        try:
            lat, lon = (float(part) for part in value.split(","))
        except ValueError as error:
            raise BadRequest(str(error)) from error
        return Endpoint(label or "Punto del mapa", lat, lon, "user", "Ubicación indicada por ti.")

    if kind == "station":
        rows = graph.query("station_detail", id=value)
        if not rows:
            raise NotFound(f"No existe la estación {value}.")
        station = rows[0]
        if station["usable"]:
            return Endpoint(
                station["name"], station["lat"], station["lon"], "bicimad",
                "Estación BiciMAD elegida directamente.",
                csv={"verdict": "yes", "text": "Sí: el CSV tiene la estación y sus coordenadas."},
                stations=[station],
            )
        return Endpoint(
            station["name"], station["lat"], station["lon"], "bicimad",
            "Esta estación no se puede usar ahora; se buscan las más cercanas.",
            csv={"verdict": "yes", "text": "Sí: el CSV tiene la estación y su estado."},
        )

    if kind == "place":
        place = wikidata.place(value)
        if place is None:
            raise NotFound(f"No se encuentra el lugar {value} en la caché de Wikidata.")
        return Endpoint(
            place["label"], place["lat"], place["lon"], "wikidata",
            "Coordenadas del lugar en Wikidata (P625).",
            csv={"verdict": "no", "text": "No: el CSV de BiciMAD no contiene lugares de interés."},
        )

    if kind == "street":
        return _street(value)

    raise BadRequest(f"Referencia no válida: {ref}")
