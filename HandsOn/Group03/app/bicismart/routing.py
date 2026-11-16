"""Planificador andar → bici → andar sobre las estaciones del grafo.

El mejor par de estaciones se elige con distancias en línea recta (× DETOUR) a velocidades
típicas; después se piden a OSRM (servidores de FOSSGIS sobre OpenStreetMap) el trazado y los
tiempos reales de los tramos elegidos. Si OSRM no responde, se muestran las estimaciones.
"""

import httpx

from . import USER_AGENT, enrich, geo, graph, trace
from .geocode import Endpoint

OSRM = "https://routing.openstreetmap.de/routed-{profile}/route/v1/driving/{coords}?overview=full&geometries=geojson"
SPEED = {"foot": 5 / 3.6, "bike": 15 / 3.6}  # m/s
DETOUR = 1.3
DOCK_S = 60  # sacar o dejar la bici en la base
CANDIDATES = 5  # estaciones que se prueban en cada extremo

# Fallos de OSRM con los que la ruta sigue, con la estimación: la red o HTTP y una respuesta con
# un formato inesperado (KeyError o IndexError si falta un dato; TypeError si "routes" es null o
# la respuesta es una lista; ValueError si no es JSON). Es el criterio de wikidata.ERRORS.
ERRORS = (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError)

_cache: dict[str, dict] = {}

Point = tuple[float, float]


def _coords(item: dict | Endpoint) -> Point:
    """(lat, lon) de una estación (fila del grafo) o de un origen o destino."""
    if isinstance(item, Endpoint):
        return (item.lat, item.lon)
    return (item["lat"], item["lon"])


def _estimated_m(a: Point, b: Point) -> float:
    """Metros estimados: línea recta × DETOUR."""
    return geo.distance_m(*a, *b) * DETOUR


def estimate(profile: str, a: Point, b: Point) -> float:
    """Segundos estimados en línea recta × DETOUR."""
    return _estimated_m(a, b) / SPEED[profile]


def route(profile: str, a: Point, b: Point) -> dict:
    """Trazado y tiempo de un tramo (OSRM route), con la geometría como lista de [lat, lon]."""
    url = OSRM.format(profile=profile, coords=f"{a[1]:.6f},{a[0]:.6f};{b[1]:.6f},{b[0]:.6f}")
    name = "ruta a pie" if profile == "foot" else "ruta en bici"
    with trace.record("osrm", name, url, cached=url in _cache) as entry:
        try:
            if url not in _cache:
                response = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
                response.raise_for_status()
                _cache[url] = response.json()["routes"][0]
            best = _cache[url]
            entry["rows"] = 1
            return {
                "duration": best["duration"],
                "distance": best["distance"],
                "geometry": [[lat, lon] for lon, lat in best["geometry"]["coordinates"]],
                "estimated": False,
            }
        except ERRORS as error:
            entry["error"] = str(error) or type(error).__name__
    meters = _estimated_m(a, b)
    return {
        "duration": meters / SPEED[profile],
        "distance": meters,
        "geometry": [list(a), list(b)],
        "estimated": True,
    }


def _candidates(endpoint: Endpoint, other: Endpoint, pool: list[dict]) -> list[dict]:
    """Estaciones que se prueban en un extremo. Si tiene estaciones propias (una calle con
    estaciones o una estación elegida), las suyas más cercanas al otro extremo; si no, las de
    `pool` más cercanas a él.
    """
    if endpoint.stations:
        return geo.nearest(endpoint.stations, other.lat, other.lon, CANDIDATES)
    return geo.nearest(pool, endpoint.lat, endpoint.lon, CANDIDATES)


def _leg(mode: str, start: str, end: str, path: dict) -> dict:
    return {"mode": mode, "from": start, "to": end, **path}


def plan(origin: Endpoint, destination: Endpoint) -> dict:
    """Mejor combinación de estación de salida y de llegada, comparada con ir andando."""
    pool = graph.query("usable_stations")
    starts = _candidates(origin, destination, pool)
    ends = _candidates(destination, origin, pool)

    def cost(start: dict, end: dict) -> float:
        walk_in = 0 if origin.stations else estimate("foot", _coords(origin), _coords(start))
        walk_out = (
            0 if destination.stations else estimate("foot", _coords(end), _coords(destination))
        )
        return walk_in + DOCK_S + estimate("bike", _coords(start), _coords(end)) + DOCK_S + walk_out

    pairs = [(cost(s, e), s, e) for s in starts for e in ends if s["id"] != e["id"]]

    # Ir andando: desde el origen (o una estación de su calle) hasta el destino (o su calle).
    departures = [_coords(s) for s in starts] if origin.stations else [_coords(origin)]
    arrivals = [_coords(e) for e in ends] if destination.stations else [_coords(destination)]
    walk_from, walk_to = min(
        ((a, b) for a in departures for b in arrivals),
        key=lambda pair: geo.distance_m(*pair[0], *pair[1]),
    )
    walk = _leg("walk", origin.label, destination.label, route("foot", walk_from, walk_to))

    bike = None
    if pairs:
        _, start, end = min(pairs, key=lambda pair: pair[0])
        legs = []
        if not origin.stations:
            path = route("foot", _coords(origin), _coords(start))
            legs.append(_leg("walk", origin.label, start["name"], path))
        path = route("bike", _coords(start), _coords(end))
        legs.append(_leg("bike", start["name"], end["name"], path))
        if not destination.stations:
            path = route("foot", _coords(end), _coords(destination))
            legs.append(_leg("walk", end["name"], destination.label, path))
        bike = {
            "duration": sum(leg["duration"] for leg in legs) + 2 * DOCK_S,
            "distance": sum(leg["distance"] for leg in legs),
            "dock": 2 * DOCK_S,  # sacar la bici y dejarla
            "legs": legs,
            "fromStation": enrich.station_summary(start),
            "toStation": enrich.station_summary(end),
            "estimated": any(leg["estimated"] for leg in legs),
        }

    return {
        "recommended": "bike" if bike and bike["duration"] < walk["duration"] else "walk",
        "bike": bike,
        "walk": walk,
    }
