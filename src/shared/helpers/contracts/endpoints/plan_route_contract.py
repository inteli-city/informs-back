from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


# Limites práticos do endpoint (definidos no plano):
# - n é o número de forms a planejar; até 50 cobre o uso real (motoverificador
#   atende ~10-20 vistorias por turno).
# - form_ids segue o mesmo limite quando o modo explícito é usado.
MAX_PLAN_ROUTE_FORMS = 50


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CoordinateSchema(RequestContractModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)


class PlanRouteRequestSchema(RequestContractModel):
    """
    Dois modos mutuamente exclusivos:

    Modo A (`n`): backend escolhe os PENDING do requester ordenados por
    priority DESC, created_at ASC e pega os primeiros N.

    Modo B (`form_ids`): cliente passa a lista exata. Backend valida que
    cada form pertence ao requester (vazamento de info bloqueado), aceita
    qualquer status, e ordena via nearest-neighbor.
    """

    start: CoordinateSchema
    end: CoordinateSchema | None = None
    n: int | None = Field(default=None, ge=1, le=MAX_PLAN_ROUTE_FORMS)
    form_ids: list[NonEmptyStr] | None = Field(
        default=None, min_length=1, max_length=MAX_PLAN_ROUTE_FORMS
    )

    @model_validator(mode="after")
    def _validate_n_xor_form_ids(self) -> "PlanRouteRequestSchema":
        provided = sum(1 for value in (self.n, self.form_ids) if value is not None)
        if provided == 0:
            raise ValueError("informe 'n' ou 'form_ids'")
        if provided > 1:
            raise ValueError("'n' e 'form_ids' são mutuamente exclusivos")
        return self


class PlanRouteFormItemSchema(ResponseContractModel):
    form_id: str
    form_title: str
    latitude: float
    longitude: float
    order: int


class PlanRouteResponseSchema(ResponseContractModel):
    ordered_forms: list[PlanRouteFormItemSchema]
    total_distance_km: float
