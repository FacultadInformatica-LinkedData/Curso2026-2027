
from typing import Literal

from pydantic import BaseModel, Field

# Tipos de instalaciones
FacilityType = Literal["library", "museum"]


class Area(BaseModel):
    uri: str
    name: str


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Address(BaseModel):
    uri: str
    street: str
    postal_code: str
    district: Area
    neighborhood: Area


class Accessibility(BaseModel):
    accessible: bool
    partially_accessible: bool
    no_info_accessibility: bool
    sign_language: bool
    tactile_paving: bool
    magnetic_induction_loop: bool


class Contact(BaseModel):
    telephone: str
    email: str


class LinkedData(BaseModel):
    wikidata_uri: str | None = None


class FacilitySummary(BaseModel):
    """Información básica para el listado y el mapa."""

    id: str
    name: str
    facility_type: FacilityType
    location: Location
    district: Area
    neighborhood: Area


class FacilityDetail(FacilitySummary):
    """Información completa de una instalación."""

    address: Address
    accessibility: Accessibility
    opening_hours: str
    transport: str
    contact: Contact
    publisher_url: str
    linked_data: LinkedData = Field(default_factory=LinkedData)
    wikidata_information: WikidataInformation | None = None


class WikidataArea(BaseModel):
    value: float
    unit: str | None = None

class WikidataInformation(BaseModel):
    """Información complementaria obtenida de Wikidata."""

    wikidata_id: str
    name: str | None = None
    description: str | None = None
    image: str | None = None
    interior_image: str | None = None
    inception: str | None = None
    architect: list[str] = Field(default_factory=list)
    founders: list[str] = Field(default_factory=list)
    wikidata_uri: str
    heritage_designations: list[str] = Field(default_factory=list)
    area: list[WikidataArea] = Field(default_factory=list)
    activity_policies: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    x_usernames: list[str] = Field(default_factory=list)