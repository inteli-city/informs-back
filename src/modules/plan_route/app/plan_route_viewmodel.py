from typing import List

from src.shared.domain.entities.form import Form
from src.shared.helpers.contracts.endpoints.plan_route_contract import PlanRouteResponseSchema


class PlanRouteViewmodel:
    def __init__(self, ordered_forms: List[Form], total_distance_km: float):
        self.ordered_forms = ordered_forms
        self.total_distance_km = total_distance_km

    def to_dict(self) -> dict:
        payload = {
            "ordered_forms": [
                {
                    "form_id": form.id,
                    "form_title": form.form_title,
                    "latitude": form.latitude,
                    "longitude": form.longitude,
                    "order": index + 1,
                }
                for index, form in enumerate(self.ordered_forms)
            ],
            "total_distance_km": round(self.total_distance_km, 3),
        }
        return PlanRouteResponseSchema.model_validate(payload).model_dump()
