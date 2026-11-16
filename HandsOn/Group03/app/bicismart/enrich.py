"""Ficha de una estación, estaciones y lugares cercanos, con BiciMAD, Callejero y Wikidata."""

from . import geo, graph, trace, wikidata
from .errors import NotFound
from .names import district_names, pretty

STATES = {
    "IN_SERVICE": "En servicio",
    "NOT_IN_SERVICE": "Fuera de servicio",
    "PLANNED": "Planificada",
    "END_OF_LIFE": "Retirada",
}


def station_summary(row: dict) -> dict:
    """Forma básica de una estación en la API, a partir de una fila del patrón `_station.rq`.

    Es la de `/api/stations`, la de las estaciones de la ruta, las fichas y las listas de
    estaciones cercanas; cada uso le añade sus claves (`distance`, `blocks`…).
    """
    return {key: row[key] for key in ("id", "name", "lat", "lon", "capacity", "usable")}


def station_card(station_id: str, nearest: int = 5, usable_only: bool = False) -> dict:
    """Ficha de una estación: sus datos de BiciMAD, el Callejero y Wikidata (`blocks`) y sus
    `nearest` estaciones más cercanas (`nearestStations`, ver `nearest_stations`).

    Cada bloque lleva su fuente (`source`): BiciMAD siempre; el Callejero si la estación está
    enlazada a una calle (bm:locatedOnStreet), y Wikidata si esa calle tiene owl:sameAs y hay
    datos suyos. Con `usable_only` solo cuentan como cercanas las que se pueden usar, que es lo
    que interesa como alternativa en una ruta. Lanza NotFound si la estación no existe.
    """
    rows = graph.query("station_detail", id=station_id)
    if not rows:
        raise NotFound(f"No existe la estación {station_id}.")
    station = rows[0]

    state = STATES.get(station["state"], station["state"])
    if not station["activated"]:
        state += " (desactivada)"
    blocks = [{
        "source": "bicimad",
        "title": "Estación",
        "items": [
            ["Estado", state],
            ["Bases", str(station["capacity"])],
            ["Bases inutilizables", str(station["unavailable"])],
            ["Coordenadas", f"{station['lat']:.5f}, {station['lon']:.5f}"],
        ],
    }]

    if station["street"]:
        districts = district_names(station["districts"])
        items = [["Calle", pretty(station["streetName"])]]
        if districts:
            items.append(["Distritos" if "," in districts else "Distrito", districts])
        if station["postalCodes"]:
            items.append(["Código postal", ", ".join(sorted(station["postalCodes"].split(",")))])
        blocks.append({"source": "callejero", "title": "Callejero", "items": items})

    if station["wikidata"] and (facts := wikidata.street_facts(wikidata.qid(station["wikidata"]))):
        blocks.append({
            "source": "wikidata",
            "title": facts.get("label") or pretty(station["streetName"]),
            "description": facts.get("description"),
            "image": facts.get("image"),
            "link": wikidata.page_url(facts["qid"]),
            "namedAfter": [
                {**person, "link": wikidata.page_url(person["qid"])}
                for person in facts.get("namedAfter", [])
            ],
        })

    return {
        **station_summary(station),
        "blocks": blocks,
        "nearestStations": nearest_stations(
            station["id"], station["lat"], station["lon"], limit=nearest, usable_only=usable_only
        ),
    }


def nearby_places(lat: float, lon: float, radius_m: float = 500, limit: int = 6) -> list[dict]:
    """Lugares de Wikidata a menos de `radius_m` metros, del más cercano al más lejano."""
    places = wikidata.places()
    with trace.record(
        "wikidata", "wikidata_places", wikidata.places_query("museo"), cached=True,
        note=f"… y una consulta igual para cada categoría: {', '.join(wikidata.CATEGORIES)}."
        + f"\nSe usan los resultados en caché y se filtran a {radius_m:.0f} m del punto.",
    ) as entry:
        found = [
            {**p, "distance": round(d), "link": wikidata.page_url(p["qid"]),
             "categories": [wikidata.CATEGORIES[c].label for c in p["categories"]]}
            for d, p in geo.by_distance(places, lat, lon, k=limit, max_m=radius_m)
        ]
        entry["rows"] = len(found)
    return found


def nearest_stations(
    station_id: str, lat: float, lon: float, limit: int = 5, usable_only: bool = False
) -> list[dict]:
    """Las `limit` estaciones más cercanas a una estación, sin contarla, en línea recta.

    Con `usable_only` solo cuentan las que se pueden usar: es lo que interesa como alternativa
    a una estación de la ruta.
    """
    stations = graph.query_cached("stations", note=(
        f"Se eligen las {limit} más cercanas" + (" utilizables" if usable_only else "")
        + f"\na la estación {station_id} en línea recta (haversine), sin contarla a ella."
    ))
    others = [s for s in stations if s["id"] != station_id and (s["usable"] or not usable_only)]
    return [
        {**station_summary(s), "distance": round(d)}
        for d, s in geo.by_distance(others, lat, lon, k=limit)
    ]


def stations_within(
    points: list[tuple[float, float]], radius_m: int, exclude: str | None = None
) -> list[dict]:
    """Estaciones a `radius_m` metros o menos de alguno de los `points`, en línea recta y de la
    más cercana a la más lejana. Incluye las que no se pueden usar.

    La distancia de cada estación es la del punto más cercano: una calle con estaciones se mide
    desde todas ellas, no desde un punto medio. `exclude` es el id de una estación que no
    cuenta: la que hace de centro.
    """
    if len(points) == 1:
        where = "de ({:.5f}, {:.5f}) ".format(*points[0])
    else:
        where = f"del más cercano de estos {len(points)} puntos:\n" + "".join(
            f"  ({lat:.5f}, {lon:.5f})\n" for lat, lon in points
        )
    stations = graph.query_cached("stations", note=(
        f"Se eligen las que están a {radius_m} m o menos\n{where}en línea recta (haversine), "
        "de la más cercana a la más lejana"
        + (f", sin contar la estación {exclude}." if exclude else ".")
    ))
    others = [s for s in stations if s["id"] != exclude]
    return [
        {**station_summary(s), "distance": round(d)}
        for d, s in geo.by_distance_to_any(others, points, max_m=radius_m)
    ]
