from typing import List, Optional

from src.shared.domain.entities.system_config import SystemConfig


class SystemConfigDynamoDTO:
    """
    Conversor entre `SystemConfig` e o item DynamoDB.

    Esquema do item (mesma `Formularios_Table`, sem GSI):
        PK = system#{system}
        SK = CONFIG
    """

    def __init__(
        self,
        system: str,
        created_at: int,
        updated_at: int,
        scope_keys: List[str],
        scope_partition_key: Optional[str],
        geofence_radius_m: Optional[float],
        allow_unassigned_forms: bool,
    ):
        self.system = system
        self.created_at = created_at
        self.updated_at = updated_at
        self.scope_keys = scope_keys
        self.scope_partition_key = scope_partition_key
        self.geofence_radius_m = geofence_radius_m
        self.allow_unassigned_forms = allow_unassigned_forms

    @staticmethod
    def from_entity(config: SystemConfig) -> "SystemConfigDynamoDTO":
        return SystemConfigDynamoDTO(
            system=config.system,
            created_at=config.created_at,
            updated_at=config.updated_at,
            scope_keys=config.scope_keys,
            scope_partition_key=config.scope_partition_key,
            geofence_radius_m=config.geofence_radius_m,
            allow_unassigned_forms=config.allow_unassigned_forms,
        )

    def to_dynamo(self) -> dict:
        return {
            "system": self.system,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scope_keys": self.scope_keys,
            "scope_partition_key": self.scope_partition_key,
            "geofence_radius_m": self.geofence_radius_m,
            "allow_unassigned_forms": self.allow_unassigned_forms,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "SystemConfigDynamoDTO":
        return SystemConfigDynamoDTO(
            system=data["system"],
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
            scope_keys=list(data.get("scope_keys") or []),
            scope_partition_key=data.get("scope_partition_key"),
            geofence_radius_m=float(data["geofence_radius_m"]) if data.get("geofence_radius_m") is not None else None,
            allow_unassigned_forms=bool(data.get("allow_unassigned_forms", False)),
        )

    def to_entity(self) -> SystemConfig:
        return SystemConfig(
            system=self.system,
            created_at=self.created_at,
            updated_at=self.updated_at,
            scope_keys=self.scope_keys,
            scope_partition_key=self.scope_partition_key,
            geofence_radius_m=self.geofence_radius_m,
            allow_unassigned_forms=self.allow_unassigned_forms,
        )

    @staticmethod
    def build_pk(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def build_sk() -> str:
        return "CONFIG"
