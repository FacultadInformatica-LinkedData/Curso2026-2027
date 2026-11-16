
import re

import httpx


WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


def extract_wikidata_id(wikidata_uri: str) -> str | None:
    """Extrae el identificador de una URI de Wikidata."""

    match = re.fullmatch(
        r"https?://(?:www\.)?wikidata\.org/entity/(Q[0-9]+)/?",
        wikidata_uri.strip(),
    )

    return match.group(1) if match else None


def build_wikidata_query(entity_id: str) -> str:
    """Construye una consulta SPARQL para Wikidata."""
    return f"""
    SELECT DISTINCT
        ?itemLabel
        ?itemDescription
        ?image
        ?interiorImage
        ?inception
        ?architectLabel
        ?founderLabel
        ?heritageDesignationLabel
        ?area
        ?areaUnitLabel
        ?activityPolicyLabel
        ?awardLabel
        ?xUsername
    WHERE {{
        VALUES ?item {{ wd:{entity_id} }}

        OPTIONAL {{ ?item wdt:P18 ?image . }}
        OPTIONAL {{ ?item wdt:P154 ?logo . }}
        OPTIONAL {{ ?item wdt:P5775 ?interiorImage . }}
        OPTIONAL {{ ?item wdt:P571 ?inception . }}
        OPTIONAL {{ ?item wdt:P84 ?architect . }}
        OPTIONAL {{ ?item wdt:P112 ?founder . }}
        OPTIONAL {{ ?item wdt:P1435 ?heritageDesignation . }}
        OPTIONAL {{
            ?item p:P2046 ?areaStatement .
            ?areaStatement psv:P2046 ?areaValueNode .
            ?areaValueNode wikibase:quantityAmount ?area .
            OPTIONAL {{
                ?areaValueNode wikibase:quantityUnit ?areaUnit .
            }}
        }}
        OPTIONAL {{ ?item wdt:P5023 ?activityPolicy . }}
        OPTIONAL {{ ?item wdt:P166 ?award . }}
        OPTIONAL {{ ?item wdt:P2002 ?xUsername . }}

        SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "es,en" .
        }}
    }}
    """


async def get_wikidata_information(
    wikidata_uri: str,
) -> dict | None:
    """Recupera toda la información disponible de una entidad."""

    entity_id = extract_wikidata_id(wikidata_uri)

    if entity_id is None:
        return None

    query = build_wikidata_query(entity_id)

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "MadridCultureApp/1.0",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            WIKIDATA_ENDPOINT,
            params={"query": query},
            headers=headers,
        )

        response.raise_for_status()

    results = response.json()["results"]["bindings"]

    if not results:
        return None

    information = {
        "wikidata_id": entity_id,
        "name": None,
        "description": None,
        "image": None,
        "interior_image": None,
        "inception": None,
        "architect": [],
        "founders": [],
        "heritage_designations": [],
        "area": [],
        "activity_policies": [],
        "awards": [],
        "x_usernames": [],
        "wikidata_uri": wikidata_uri,
    }

    for result in results:
        # Nombre
        if information["name"] is None:
            value = result.get("itemLabel")
            if value:
                information["name"] = value["value"]

        # Descripción
        if information["description"] is None:
            value = result.get("itemDescription")
            if value:
                information["description"] = value["value"]

        # Imagen interior
        if information["interior_image"] is None:
            value = result.get("interiorImage")
            if value:
                information["interior_image"] = value["value"]

        # Fundadores
        value = result.get("founderLabel")
        if value:
            founder = value["value"]
            if founder not in information["founders"]:
                information["founders"].append(founder)

        # Imagen: un único valor.
        if information["image"] is None:
            value = result.get("image")
            if value:
                information["image"] = value["value"]

        # Fecha de creación: un único valor.
        if information["inception"] is None:
            value = result.get("inception")
            if value:
                information["inception"] = value["value"]

        # Arquitectos: múltiples valores.
        value = result.get("architectLabel")
        if value:
            architect = value["value"]

            if architect not in information["architect"]:
                information["architect"].append(architect)

        # Declaraciones de patrimonio
        value = result.get("heritageDesignationLabel")
        if value:
            designation = value["value"]

            if designation not in information["heritage_designations"]:
                information["heritage_designations"].append(designation)


        # Superficie
        if "area" in result:
            area = {
                "value": float(result["area"]["value"]),
                "unit": result.get("areaUnitLabel", {}).get("value"),
            }

            if area not in information["area"]:
                information["area"].append(area)


        # Políticas de actividades
        value = result.get("activityPolicyLabel")
        if value:
            policy = value["value"]

            if policy not in information["activity_policies"]:
                information["activity_policies"].append(policy)


        # Premios recibidos
        value = result.get("awardLabel")
        if value:
            award = value["value"]

            if award not in information["awards"]:
                information["awards"].append(award)


        # Usuarios de X
        value = result.get("xUsername")
        if value:
            username = value["value"]

            if username not in information["x_usernames"]:
                information["x_usernames"].append(username)

    return information
