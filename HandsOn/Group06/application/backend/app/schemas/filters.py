
from typing import Literal

from pydantic import BaseModel, model_validator

from app.schemas.facility import FacilityType

# Estado de accesibilidad
AccessibilityStatus = Literal[
    "accessible",
    "partial"
]

AccessibilityFeature = Literal[
    "sign_language",
    "tactile_paving",
    "magnetic_induction_loop",
]


class FacilityFilters(BaseModel):
    query: str | None = None
    facility_types: list[FacilityType] | None = None
    district: str | None = None
    neighborhood: str | None = None

    accessibility_status: list[AccessibilityStatus] | None = None
    accessibility_features: list[AccessibilityFeature] | None = None

    @model_validator(mode="after")
    def validate_accessibility_features(self):
        if self.accessibility_features and not self.accessibility_status:
            raise ValueError(
                "Para filtrar por características debes seleccionar "
                "Accesible o Parcialmente accesible."
            )

        return self
