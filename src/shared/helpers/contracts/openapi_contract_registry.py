from dataclasses import dataclass
from typing import Optional, Type

from pydantic import BaseModel

from src.shared.helpers.contracts.endpoints.assign_form_contract import AssignFormRequestSchema, AssignFormResponseSchema
from src.shared.helpers.contracts.endpoints.cancel_form_contract import CancelFormRequestSchema, CancelFormResponseSchema
from src.shared.helpers.contracts.endpoints.claim_form_contract import ClaimFormResponseSchema
from src.shared.helpers.contracts.endpoints.create_form_contract import CreateFormRequestSchema, CreateFormResponseSchema
from src.shared.helpers.contracts.endpoints.create_template_contract import (
    CreateTemplateRequestSchema,
    CreateTemplateResponseSchema,
)
from src.shared.helpers.contracts.endpoints.get_all_forms_contract import GetAllFormsResponseSchema
from src.shared.helpers.contracts.endpoints.get_all_templates_contract import GetAllTemplatesResponseSchema
from src.shared.helpers.contracts.endpoints.get_app_config_contract import GetAppConfigResponseSchema
from src.shared.helpers.contracts.endpoints.app_config_admin_contract import (
    GetAppConfigAdminResponseSchema,
    PutAppConfigLayerRequestSchema,
    PutDefaultAppConfigResponseSchema,
    PutSystemAppConfigResponseSchema,
)
from src.shared.helpers.contracts.endpoints.get_form_contract import GetFormResponseSchema
from src.shared.helpers.contracts.endpoints.get_template_contract import GetTemplateResponseSchema
from src.shared.helpers.contracts.endpoints.location_history_contract import (
    LocationHistoryRequestSchema,
    LocationHistoryResponseSchema,
)
from src.shared.helpers.contracts.endpoints.plan_route_contract import (
    PlanRouteRequestSchema,
    PlanRouteResponseSchema,
)
from src.shared.helpers.contracts.endpoints.profile_contract import (
    CreateProfileRequestSchema,
    CreateProfileResponseSchema,
    DeleteProfileResponseSchema,
    LoginProfileResponseSchema,
    UpdateProfileRequestSchema,
    UpdateProfileResponseSchema,
)
from src.shared.helpers.contracts.endpoints.refresh_presign_contract import (
    RefreshPresignRequestSchema,
    RefreshPresignResponseSchema,
)
from src.shared.helpers.contracts.endpoints.release_form_contract import ReleaseFormResponseSchema
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
        path="/forms/{formId}/files/refresh-presign",
        method="post",
        tag="Forms",
        summary="Renova as presigned URLs de arquivos já registrados no formulário",
        success_status_code=200,
        request_model=RefreshPresignRequestSchema,
        response_model=RefreshPresignResponseSchema,
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
        path="/forms/{formId}/claim",
        method="post",
        tag="Forms",
        summary="Reivindica uma OS aberta no pool (especificação Uberlândia)",
        success_status_code=200,
        response_model=ClaimFormResponseSchema,
    ),
    EndpointContract(
        path="/forms/{formId}/release",
        method="post",
        tag="Forms",
        summary="Devolve uma OS ao pool, descartando o conteúdo (especificação Uberlândia)",
        success_status_code=200,
        response_model=ReleaseFormResponseSchema,
    ),
    EndpointContract(
        path="/forms/{formId}/assign",
        method="post",
        tag="Forms",
        summary="Gestor/Fiscal atribui uma OS do pool a um usuário (especificação Uberlândia)",
        success_status_code=200,
        request_model=AssignFormRequestSchema,
        response_model=AssignFormResponseSchema,
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
        path="/profiles",
        method="post",
        tag="Profiles",
        summary="Admin cria perfil (ADMIN ou INSPECTOR)",
        success_status_code=201,
        request_model=CreateProfileRequestSchema,
        response_model=CreateProfileResponseSchema,
    ),
    EndpointContract(
        path="/profiles/login",
        method="post",
        tag="Profiles",
        summary="Login: retorna perfil do requester (auto-cria como INSPECTOR se não existir)",
        success_status_code=200,
        response_model=LoginProfileResponseSchema,
    ),
    EndpointContract(
        path="/profiles/{user_id}",
        method="delete",
        tag="Profiles",
        summary="Soft delete de perfil (admin)",
        success_status_code=200,
        response_model=DeleteProfileResponseSchema,
    ),
    EndpointContract(
        path="/profiles/{user_id}",
        method="put",
        tag="Profiles",
        summary="Admin atualiza role e scope de um perfil (integração Apex)",
        success_status_code=200,
        request_model=UpdateProfileRequestSchema,
        response_model=UpdateProfileResponseSchema,
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
        path="/app-config",
        method="get",
        tag="Config",
        summary="Configuração efetiva da aplicação: o padrão e a de cada sistema do usuário",
        success_status_code=200,
        response_model=GetAppConfigResponseSchema,
    ),
    EndpointContract(
        path="/app-config/admin",
        method="get",
        tag="Config",
        summary="Admin: camadas da configuração (padrão e sistemas que o usuário administra) e o esquema do editor",
        success_status_code=200,
        response_model=GetAppConfigAdminResponseSchema,
    ),
    EndpointContract(
        path="/app-config/default",
        method="put",
        tag="Config",
        summary="Admin da plataforma: grava o padrão da aplicação",
        success_status_code=200,
        request_model=PutAppConfigLayerRequestSchema,
        response_model=PutDefaultAppConfigResponseSchema,
    ),
    EndpointContract(
        path="/app-config/systems/{system}",
        method="put",
        tag="Config",
        summary="Admin do sistema: grava as diferenças do sistema em relação ao padrão",
        success_status_code=200,
        request_model=PutAppConfigLayerRequestSchema,
        response_model=PutSystemAppConfigResponseSchema,
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
    EndpointContract(
        path="/locations/history",
        method="get",
        tag="Locations",
        summary="Histórico de localização de um inspector no período (admin)",
        success_status_code=200,
        request_model=LocationHistoryRequestSchema,
        response_model=LocationHistoryResponseSchema,
    ),
]


def get_endpoint_contracts() -> list[EndpointContract]:
    return list(_CONTRACTS)
