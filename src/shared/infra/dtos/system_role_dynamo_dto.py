from typing import List

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action


class SystemRoleDynamoDTO:
    """
    Conversor entre SystemRole e o item DynamoDB (tabela de Profiles).

    Esquema do item:
        PK = system#{system}
        SK = role#{role_id}

    Query PK = system#{system}, SK begins_with role# → roles do sistema.
    """

    SK_PREFIX = "role#"

    def __init__(
        self,
        system: str,
        role_id: str,
        name: str,
        actions: List[str],
        is_default: bool,
        created_at: int,
        updated_at: int,
    ):
        self.system = system
        self.role_id = role_id
        self.name = name
        self.actions = actions
        self.is_default = is_default
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_entity(role: SystemRole) -> "SystemRoleDynamoDTO":
        return SystemRoleDynamoDTO(
            system=role.system,
            role_id=role.role_id,
            name=role.name,
            actions=[action.value for action in role.actions],
            is_default=role.is_default,
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    def to_dynamo(self) -> dict:
        return {
            "system": self.system,
            "role_id": self.role_id,
            "name": self.name,
            "actions": self.actions,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "SystemRoleDynamoDTO":
        return SystemRoleDynamoDTO(
            system=data["system"],
            role_id=data["role_id"],
            name=data["name"],
            actions=list(data.get("actions") or []),
            is_default=bool(data.get("is_default", False)),
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
        )

    def to_entity(self) -> SystemRole:
        known = {action.value for action in Action}
        return SystemRole(
            system=self.system,
            role_id=self.role_id,
            name=self.name,
            # Ação que saiu do catálogo deixa de valer, sem quebrar a leitura.
            actions=[Action(value) for value in self.actions if value in known],
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def build_pk(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def build_sk(role_id: str) -> str:
        return f"{SystemRoleDynamoDTO.SK_PREFIX}{role_id}"
