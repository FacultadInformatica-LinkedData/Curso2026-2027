"""Distancias en línea recta entre coordenadas WGS84 y orden por distancia.

Lo que en Python mide u ordena por distancia pasa por aquí. Los elementos son diccionarios con
claves `lat` y `lon` (estaciones, lugares…).
"""

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_000


def distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia haversine en metros."""
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(sqrt(a))


def by_distance_to_any(
    items: list[dict], points: list[tuple[float, float]], k: int | None = None,
    max_m: float | None = None,
) -> list[tuple[float, dict]]:
    """Pares (metros, elemento) del más cercano al más lejano, midiendo cada elemento desde el
    más cercano de los `points`.

    Con `max_m` solo quedan los que están a esa distancia o menos, y con `k`, los `k` primeros.
    A igual distancia se respeta el orden de `items`.
    """
    pairs = sorted(
        (
            (min(distance_m(lat, lon, item["lat"], item["lon"]) for lat, lon in points), item)
            for item in items
        ),
        key=lambda pair: pair[0],
    )
    if max_m is not None:
        pairs = [pair for pair in pairs if pair[0] <= max_m]
    return pairs[:k]


def by_distance(
    items: list[dict], lat: float, lon: float, k: int | None = None, max_m: float | None = None
) -> list[tuple[float, dict]]:
    """Pares (metros, elemento) del más cercano al más lejano a un punto.

    `k` y `max_m` funcionan como en `by_distance_to_any`.
    """
    return by_distance_to_any(items, [(lat, lon)], k, max_m)


def nearest(items: list[dict], lat: float, lon: float, k: int) -> list[dict]:
    """Los `k` elementos más cercanos a un punto."""
    return [item for _, item in by_distance(items, lat, lon, k)]


def centroid(items: list[dict]) -> tuple[float, float]:
    return (sum(i["lat"] for i in items) / len(items), sum(i["lon"] for i in items) / len(items))
