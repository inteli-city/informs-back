from typing import Any, Dict, Optional

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.infra.dtos.system_config_dynamo_dto import _from_dynamo_value


class DefaultAppConfigDynamoDTO:
    """
    Conversor entre `DefaultAppConfig` e o item DynamoDB.

    Esquema do item (mesma `Formularios_Table`, sem GSI):
        PK = app_config#DEFAULT
        SK = CONFIG
    """

    def __init__(self, values: Dict[str, Any], version: int, updated_at: int, updated_by: Optional[str]):
        self.values = values
        self.version = version
        self.updated_at = updated_at
        self.updated_by = updated_by

    @staticmethod
    def from_entity(config: DefaultAppConfig) -> "DefaultAppConfigDynamoDTO":
        return DefaultAppConfigDynamoDTO(
            values=config.values,
            version=config.version,
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        )

    def to_dynamo(self) -> dict:
        return {
            "values": self.values,
            "version": self.version,
            "updated_at": self.updated_at,
            "updated_by": self.updated_by,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "DefaultAppConfigDynamoDTO":
        return DefaultAppConfigDynamoDTO(
            values=_from_dynamo_value(data.get("values") or {}),
            version=int(data.get("version", 0)),
            updated_at=int(data["updated_at"]),
            updated_by=data.get("updated_by"),
        )

    def to_entity(self) -> DefaultAppConfig:
        return DefaultAppConfig(
            values=self.values,
            version=self.version,
            updated_at=self.updated_at,
            updated_by=self.updated_by,
        )

    @staticmethod
    def build_pk() -> str:
        return "app_config#DEFAULT"

    @staticmethod
    def build_sk() -> str:
        return "CONFIG"
