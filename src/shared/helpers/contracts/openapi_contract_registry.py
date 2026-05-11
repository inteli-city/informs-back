from dataclasses import dataclass
from typing import Optional, Type

from pydantic import BaseModel

from src.shared.helpers.contracts.endpoints.cancel_form_contract import CancelFormRequestSchema, CancelFormResponseSchema
from src.shared.helpers.contracts.endpoints.create_form_contract import CreateFormRequestSchema, CreateFormResponseSchema
from src.shared.helpers.contracts.endpoints.create_template_contract import (
    CreateTemplateRequestSchema,
    CreateTemplateResponseSchema,
)
from src.shared.helpers.contracts.endpoints.get_all_forms_contract import GetAllFormsResponseSchema
from src.shared.helpers.contracts.endpoints.get_all_templates_contract import GetAllTemplatesResponseSchema
from src.shared.helpers.contracts.endpoints.get_form_contract import GetFormResponseSchema
from src.shared.helpers.contracts.endpoints.get_template_contract import GetTemplateResponseSchema
from src.shared.helpers.contracts.endpoints.plan_route_contract import (
    PlanRouteRequestSchema,
    PlanRouteResponseSchema,
)
from src.shared.helpers.contracts.endpoints.start_form_contract import StartFormRequestSchema
from src.shared.helpers.contracts.endpoints.submit_form_contract import SubmitFormRequestSchema, SubmitFormResponseSchema
from src.shared.helpers.contracts.endpoints.sync_origin_callback_contract import (
    SyncCallbackRequestSchema,
    SyncCallbackResponseSchema,
)
from src.shared.helpers.contracts.endpoints.update_template_contract import (
    UpdateTemplateRequestSchema,
    UpdateTemplateResponseSchema,
)


@dataclass(frozen=True)
class EndpointContract:
    path: str
    method: str
    tag: str
    summary: str
    success_status_code: int
    request_model: Optional[Type[BaseModel]] = None
    response_model: Optional[Type[BaseModel]] = None


_CONTRACTS = [
    EndpointContract(
        path="/forms",
        method="post",
        tag="Forms",
        summary="Criação de novo formulário",
        success_status_code=201,
        request_model=CreateFormRequestSchema,
        response_model=CreateFormResponseSchema,
    ),
    EndpointContract(
        path="/forms",
        method="get",
        tag="Forms",
        summary="Listagem de formulários com filtros",
        success_status_code=200,
        response_model=GetAllFormsResponseSchema,
    ),
    EndpointContract(
        path="/forms/{formId}",
        method="get",
        tag="Forms",
        summary="Consulta formulário por ID",
        success_status_code=200,
        response_model=GetFormResponseSchema,
    ),
    EndpointContract(
        path="/forms/{formId}/start",
        method="post",
        tag="Forms",
        summary="Inicia o preenchimento (Preenchedor)",
        success_status_code=204,
        request_model=StartFormRequestSchema,
    ),
    EndpointContract(
        path="/forms/{formId}/submit",
        method="post",
        tag="Forms",
        summary="Submete o formulário preenchido",
        success_status_code=200,
        request_model=SubmitFormRequestSchema,
        response_model=SubmitFormResponseSchema,
    ),
    EndpointContract(
        path="/forms/{formId}/cancel",
        method="post",
        tag="Forms",
        summary="Cancela o formulário",
        success_status_code=200,
        request_model=CancelFormRequestSchema,
        response_model=CancelFormResponseSchema,
    ),
    EndpointContract(
        path="/forms/route-plan",
        method="post",
        tag="Forms",
        summary="Planeja sequência de visita dos formulários PENDING do requester",
        success_status_code=200,
        request_model=PlanRouteRequestSchema,
        response_model=PlanRouteResponseSchema,
    ),
    EndpointContract(
        path="/templates",
        method="post",
        tag="Templates",
        summary="Criação de novo template de formulário",
        success_status_code=201,
        request_model=CreateTemplateRequestSchema,
        response_model=CreateTemplateResponseSchema,
    ),
    EndpointContract(
        path="/templates/{template_id}",
        method="put",
        tag="Templates",
        summary="Altera um template",
        success_status_code=200,
        request_model=UpdateTemplateRequestSchema,
        response_model=UpdateTemplateResponseSchema,
    ),
    EndpointContract(
        path="/templates/{template_id}",
        method="get",
        tag="Templates",
        summary="Consulta template por ID",
        success_status_code=200,
        response_model=GetTemplateResponseSchema,
    ),
    EndpointContract(
        path="/templates",
        method="get",
        tag="Templates",
        summary="Listagem de templates",
        success_status_code=200,
        response_model=GetAllTemplatesResponseSchema,
    ),
    EndpointContract(
        path="/forms/sync-origin/callback",
        method="post",
        tag="Sync",
        summary="Callback de falhas de sincronização de formulários",
        success_status_code=200,
        request_model=SyncCallbackRequestSchema,
        response_model=SyncCallbackResponseSchema,
    ),
]


def get_endpoint_contracts() -> list[EndpointContract]:
    return list(_CONTRACTS)
