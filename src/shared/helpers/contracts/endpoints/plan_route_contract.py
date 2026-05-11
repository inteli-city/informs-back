from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


# Limites práticos do endpoint (definidos no plano):
# - n é o número de forms a planejar; até 50 cobre o uso real (motoverificador
#   atende ~10-20 vistorias por turno).
MAX_PLAN_ROUTE_FORMS = 50


class CoordinateSchema(RequestContractModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class PlanRouteRequestSchema(RequestContractModel):
    start: CoordinateSchema
    end: CoordinateSchema | None = None
    n: int = Field(ge=1, le=MAX_PLAN_ROUTE_FORMS)


class PlanRouteFormItemSchema(ResponseContractModel):
    form_id: str
    form_title: str
    latitude: float
    longitude: float
    order: int


class PlanRouteResponseSchema(ResponseContractModel):
    ordered_forms: list[PlanRouteFormItemSchema]
    total_distance_km: float
