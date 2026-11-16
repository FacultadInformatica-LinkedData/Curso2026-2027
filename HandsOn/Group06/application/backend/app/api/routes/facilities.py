from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

import httpx
from rdflib import Graph

from app.rdf.queries import (
    get_facilities,
    get_facility_by_id,
)

from app.wikidata.client import get_wikidata_information

from app.schemas import (
    FacilitySummary,
    FacilityDetail,
    FacilityFilters,
    NearbySearch,
    WikidataInformation 
)


router = APIRouter(
    prefix="/facilities",
    tags=["Facilities"],
)


@router.get("", response_model=list[FacilitySummary])
def list_facilities(
    request: Request, 
    filters: Annotated[FacilityFilters, Query()],
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    radius: float = Query(default=1.0)
):
    """Devuelve todas las bibliotecas y museos (sin detalles)"""

    graph: Graph = request.app.state.rdf_graph

    # Comprobar los parámetros de búsqueda por cercanía.
    nearby = None

    if latitude is not None or longitude is not None:

        if latitude is None or longitude is None:
            raise HTTPException(
                status_code=400,
                detail="Debes proporcionar latitud y longitud conjuntamente.",
            )

        nearby = NearbySearch(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
        )

    return get_facilities(graph, filters, nearby)


@router.get("/{facility_id:path}", response_model=FacilityDetail)
async def facility_detail(
    facility_id: str,
    request: Request,
):
    """Devuelve los detalles de una instalación."""

    graph: Graph = request.app.state.rdf_graph

    facility = get_facility_by_id(
        graph,
        facility_id,
    )

    if facility is None:
        raise HTTPException(
            status_code=404,
            detail="Facility not found",
        )

    # Consultar Wikidata si existe una URI vinculada.
    wikidata_uri = facility.linked_data.wikidata_uri

    print("URI de Wikidata:", wikidata_uri)

    if wikidata_uri is not None:
        try:
            information = await get_wikidata_information(wikidata_uri)

            print("Información recuperada:", information)

            if information is not None:
                facility = facility.model_copy(
                    update={
                        "wikidata_information": WikidataInformation(
                            **information
                        )
                    }
                )

        except Exception as error:
            print("Error consultando Wikidata:", repr(error))

    return facility
