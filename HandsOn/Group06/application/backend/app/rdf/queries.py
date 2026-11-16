

from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

from app.rdf.namespaces import MC, SCHEMA, RES
from app.schemas import (
    Accessibility,
    Address,
    Area,
    Contact,
    FacilityDetail,
    FacilitySummary,
    Location,
    LinkedData,
    FacilityFilters,
    NearbySearch
)

from app.services.geo import _calculate_distance

# --------------------------------------------------
# Fragmento común: información de las instalaciones
# --------------------------------------------------

FACILITY_COMMON_PATTERN = """

    ?facility rdf:type ?facilityClass .

    ?facility schema:name ?name .
    ?facility schema:latitude ?latitude .
    ?facility schema:longitude ?longitude .

    ?facility mc:hasAddress ?address .

    ?address mc:locatedInDistrict ?district .
    ?district schema:name ?district_name .

    ?address mc:locatedInNeighborhood ?neighborhood .
    ?neighborhood schema:name ?neighborhood_name .

    ?facility mc:hasAccessibility ?accessibility .

    ?accessibility mc:accessible ?accessible .
    ?accessibility mc:partiallyAccessible ?partially_accessible .
    ?accessibility mc:noInfoAccessibility ?no_info_accessibility .
    ?accessibility mc:signLanguage ?sign_language .
    ?accessibility mc:tactilePaving ?tactile_paving .
    ?accessibility mc:magneticInductionLoop ?magnetic_induction_loop .
"""

# --------------------------------------------------
# Detalles de una instalación
# --------------------------------------------------

FACILITY_DETAIL_QUERY = """
    SELECT
        ?facility
        ?facilityClass
        ?name
        ?latitude
        ?longitude
        ?address
        ?street
        ?postal_code
        ?district
        ?district_name
        ?neighborhood
        ?neighborhood_name
        ?opening_hours
        ?transport
        ?telephone
        ?email
        ?publisher_url
        ?same_as
        ?accessible
        ?partially_accessible
        ?no_info_accessibility
        ?sign_language
        ?tactile_paving
        ?magnetic_induction_loop

    WHERE {
        VALUES ?facilityClass {
            mc:Library
            mc:Museum
        }

        ?facility rdf:type ?facilityClass .

        ?facility schema:name ?name .
        ?facility schema:latitude ?latitude .
        ?facility schema:longitude ?longitude .

        ?facility mc:hasAddress ?address .

        ?address mc:locatedInDistrict ?district .
        ?district schema:name ?district_name .

        ?address mc:locatedInNeighborhood ?neighborhood .
        ?neighborhood schema:name ?neighborhood_name .

        ?facility mc:hasAccessibility ?accessibility .

        ?accessibility mc:accessible ?accessible .
        ?accessibility mc:partiallyAccessible ?partially_accessible .
        ?accessibility mc:noInfoAccessibility ?no_info_accessibility .
        ?accessibility mc:signLanguage ?sign_language .
        ?accessibility mc:tactilePaving ?tactile_paving .
        ?accessibility mc:magneticInductionLoop ?magnetic_induction_loop .

        ?address mc:streetAddress ?street .
        ?address mc:postalCode ?postal_code .

        ?facility schema:openingHours ?opening_hours .
        ?facility mc:transport ?transport .
        ?facility schema:telephone ?telephone .
        ?facility mc:email ?email .
        ?facility schema:url ?publisher_url .

        OPTIONAL {
            ?facility owl:sameAs ?same_as .
        }
    }
"""


# --------------------------------------------------
# Funciones auxiliares
# --------------------------------------------------

NAMESPACES = {
    "rdf": RDF,
    "rdfs": RDFS,
    "owl": OWL,
    "mc": MC,
    "schema": SCHEMA,
}


def _get_value(row: dict, key: str):
    """Obtiene el valor Python de una variable SPARQL."""

    value = row.get(key)

    if value is None:
        return None

    return value.toPython()


def _get_area(row: dict, uri_key: str, name_key: str) -> Area | None:
    """Construye un área administrativa si existe su URI."""

    uri = row.get(uri_key)

    return Area(
        uri=str(uri),
        name=_get_value(row, name_key),
    )


def _get_location(row: dict) -> Location | None:
    """Construye las coordenadas si ambas están disponibles."""

    latitude = _get_value(row, "latitude")
    longitude = _get_value(row, "longitude")

    return Location(
        latitude=float(latitude),
        longitude=float(longitude),
    )


def _get_facility_type(value) -> str:
    """Convierte la clase RDF en el tipo utilizado por la API."""

    if str(value) == str(MC.Library):
        return "library"

    return "museum"


def _row_to_dict(row) -> dict:
    """Convierte las variables de una fila SPARQL en un diccionario."""

    return {
        str(variable): value
        for variable, value in row.asdict().items()
    }


def build_facilities_query(
    filters: FacilityFilters | None = None,
) -> tuple[str, dict]:
    """Construye la consulta SPARQL según los filtros seleccionados."""

    conditions = []
    bindings = {}

    facility_classes = [MC.Library, MC.Museum]

    if filters is not None:

        # Filtro por tipo
        if filters.facility_types:
            facility_classes = [
                MC.Library
                if facility_type == "library"
                else MC.Museum
                for facility_type in filters.facility_types
            ]

        # Filtro por nombre
        if filters.query:
            conditions.append(
                "FILTER(CONTAINS(LCASE(STR(?name)), LCASE(STR(?search))))"
            )
            bindings["search"] = Literal(filters.query)

        # Filtro por distrito
        if filters.district:
            conditions.append(
                "FILTER(?district = ?selected_district)"
            )
            bindings["selected_district"] = URIRef(filters.district)

        # Filtro por barrio
        if filters.neighborhood:
            conditions.append(
                "FILTER(?neighborhood = ?selected_neighborhood)"
            )
            bindings["selected_neighborhood"] = URIRef(
                filters.neighborhood
            )

        # Filtro por estado de accesibilidad
        if filters.accessibility_status:
            status_conditions = []

            if "accessible" in filters.accessibility_status:
                status_conditions.append("?accessible = true")

            if "partial" in filters.accessibility_status:
                status_conditions.append(
                    "?partially_accessible = true"
                )

            conditions.append(
                "FILTER(" + " || ".join(status_conditions) + ")"
            )

        # Filtro por características de accesibilidad
        if filters.accessibility_features:
            feature_variables = {
                "sign_language": "?sign_language",
                "tactile_paving": "?tactile_paving",
                "magnetic_induction_loop": "?magnetic_induction_loop",
            }

            for feature in filters.accessibility_features:
                conditions.append(
                    f"FILTER({feature_variables[feature]} = true)"
                )

    query = """
        SELECT DISTINCT
            ?facility
            ?facilityClass
            ?name
            ?latitude
            ?longitude
            ?district
            ?district_name
            ?neighborhood
            ?neighborhood_name
            ?accessible
            ?partially_accessible
            ?no_info_accessibility
            ?sign_language
            ?tactile_paving
            ?magnetic_induction_loop

        WHERE {
            VALUES ?facilityClass {
                """ + " ".join(
                    f"<{uri}>" for uri in facility_classes
                ) + """
            }

    """ + FACILITY_COMMON_PATTERN + """

    """ + "\n".join(conditions) + """

        }
    """

    return query, bindings


def _within_distance(
    facility: FacilitySummary, 
    nearby: NearbySearch
) -> tuple[bool, float]:
    """Comprueba si una instalación está en las distancias especificadas"""

    distance = _calculate_distance(
        nearby.latitude,
        nearby.longitude,
        facility.location.latitude,
        facility.location.longitude,
    )

    # Comprobar si está dentro del radio.
    return distance <= nearby.radius, distance

# --------------------------------------------------
# Función para obtener el listado
# --------------------------------------------------

def get_facilities(
    graph: Graph, 
    filters: FacilityFilters | None = None, 
    nearby: NearbySearch | None = None
) -> list[FacilitySummary]:
    """Obtiene los datos básicos de bibliotecas y museos."""

    query, bindings = build_facilities_query(filters)

    results = graph.query(
        query,
        initNs=NAMESPACES,
        initBindings=bindings,
    )

    facilities = []

    for result in results:
        row = _row_to_dict(result)

        facility = FacilitySummary(
            id=str(row["facility"]),
            name=str(_get_value(row, "name")),
            facility_type=_get_facility_type(row["facilityClass"]),
            location=_get_location(row),
            district=_get_area(row, "district", "district_name"),
            neighborhood=_get_area(
                row,
                "neighborhood",
                "neighborhood_name",
            ),
        )

        # Aplicar filtro distancia solamente si se ha proporcionado
        if nearby is not None:
            is_within_distance, _ = _within_distance(facility, nearby)

            if not is_within_distance:
                continue

        facilities.append(facility)

    return facilities


# --------------------------------------------------
# Función para obtener el detalle
# --------------------------------------------------

def get_facility_by_id(
    graph: Graph,
    facility_id: str
) -> FacilityDetail | None:
    """Obtiene toda la información de una instalación concreta."""

    results = graph.query(
        FACILITY_DETAIL_QUERY,
        initNs=NAMESPACES,
        initBindings={
            "facility": URIRef(f"{RES}{facility_id}"),
        },
    )

    result = next(iter(results), None)

    if result is None:
        return None

    row = _row_to_dict(result)

    address = Address(
        uri=str(row["address"]),
        street=_get_value(row, "street"),
        postal_code=_get_value(row, "postal_code"),
        district=_get_area(row, "district", "district_name"),
        neighborhood=_get_area(
            row,
            "neighborhood",
            "neighborhood_name",
        ),
    )

    accessibility = Accessibility(
        accessible=_get_value(row, "accessible"),
        partially_accessible=_get_value(
            row,
            "partially_accessible",
        ),
        no_info_accessibility=_get_value(
            row,
            "no_info_accessibility",
        ),
        sign_language=_get_value(row, "sign_language"),
        tactile_paving=_get_value(row, "tactile_paving"),
        magnetic_induction_loop=_get_value(
            row,
            "magnetic_induction_loop",
        ),
    )

    return FacilityDetail(
        id=str(row["facility"]),
        name=str(_get_value(row, "name")),
        facility_type=_get_facility_type(row["facilityClass"]),
        location=_get_location(row),
        district=_get_area(row, "district", "district_name"),
        neighborhood=_get_area(
            row,
            "neighborhood",
            "neighborhood_name",
        ),
        address=address,
        accessibility=accessibility,
        opening_hours=_get_value(row, "opening_hours"),
        transport=_get_value(row, "transport"),
        contact=Contact(
            telephone=_get_value(row, "telephone"),
            email=_get_value(row, "email"),
        ),
        publisher_url=str(row["publisher_url"]),
        linked_data=LinkedData(
            wikidata_uri=(
                str(row["same_as"])
                if row.get("same_as") is not None
                else None
            )
        ),
    )