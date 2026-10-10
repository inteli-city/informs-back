from src.shared.domain.entities.app_config import AppConfig
from src.shared.helpers.contracts.base import ResponseContractModel


class DefaultAppConfigResponseSchema(ResponseContractModel):
    version: str
    config: AppConfig


class SystemAppConfigResponseSchema(ResponseContractModel):
    system: str
    version: str
    config: AppConfig


class GetAppConfigResponseSchema(ResponseContractModel):
    default: DefaultAppConfigResponseSchema
    systems: list[SystemAppConfigResponseSchema]
