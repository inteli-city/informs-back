from typing import Any

from pydantic import Field

from src.shared.domain.entities.app_config import AppConfig
from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class AppConfigLayerResponseSchema(ResponseContractModel):
    # Só as chaves que a camada muda — o que o Admin edita.
    values: dict[str, Any]
    version: int


class AdminSystemAppConfigResponseSchema(AppConfigLayerResponseSchema):
    system: str
    # Padrão + diferenças do sistema: o que o app de campo recebe.
    effective: AppConfig


class GetAppConfigAdminResponseSchema(ResponseContractModel):
    # JSON Schema do AppConfig (títulos e descrições em português): o editor do
    # Admin é gerado a partir dele, então uma chave nova aparece sem tela nova.
    config_schema: dict[str, Any]
    # Defaults do esquema — o app como ele é hoje, antes de qualquer camada.
    schema_defaults: AppConfig
    default_layer: AppConfigLayerResponseSchema
    can_edit_default: bool
    systems: list[AdminSystemAppConfigResponseSchema]


class PutAppConfigLayerRequestSchema(RequestContractModel):
    values: dict[str, Any]
    # Versão que a pessoa editou. Se alguém salvou antes, o PUT é recusado (409)
    # em vez de apagar a alteração do outro.
    base_version: int = Field(ge=0)


class PutDefaultAppConfigResponseSchema(AppConfigLayerResponseSchema):
    pass


class PutSystemAppConfigResponseSchema(AdminSystemAppConfigResponseSchema):
    pass
