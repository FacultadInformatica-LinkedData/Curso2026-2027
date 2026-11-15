
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

from app.schemas.facility import FacilitySummary, Location


def validate_radius(value: float) -> float:
    if value not in (0.5, 1.0, 2.0, 5.0):
        raise ValueError("El radio debe ser 0.5, 1, 2 o 5 km.")
    return value


class NearbySearch(BaseModel):
    """Parámetros para buscar instalaciones cercanas."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    radius: Annotated[float, AfterValidator(validate_radius)] = 1.0