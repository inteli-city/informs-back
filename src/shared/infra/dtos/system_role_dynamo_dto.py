from typing import List, Optional

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.assignment_option_enum import (
    DEFAULT_ASSIGNMENT,
    DEFAULT_ASSIGNMENT_OPTIONS,
    AssignmentOption,
)
from src.shared.domain.enums.home_tab_enum import HomeTab


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
        home_tab: str = HomeTab.LIST.value,
        assignment_options: Optional[List[str]] = None,
        default_assignment: Optional[str] = None,
    ):
        self.system = system
        self.role_id = role_id
        self.name = name
        self.actions = actions
        self.is_default = is_default
        self.created_at = created_at
        self.updated_at = updated_at
        self.home_tab = home_tab
        self.assignment_options = assignment_options
        self.default_assignment = default_assignment

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
            home_tab=role.home_tab.value,
            assignment_options=[option.value for option in role.assignment_options],
            default_assignment=role.default_assignment.value,
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
            "home_tab": self.home_tab,
            "assignment_options": self.assignment_options,
            "default_assignment": self.default_assignment,
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
            # Role gravado antes da aba inicial existir: abre na lista.
            home_tab=data.get("home_tab") or HomeTab.LIST.value,
            # Role gravado antes das opções de destino: o comportamento de antes.
            assignment_options=list(data["assignment_options"]) if data.get("assignment_options") else None,
            default_assignment=data.get("default_assignment"),
        )

    def to_entity(self) -> SystemRole:
        known = {action.value for action in Action}
        known_tabs = {tab.value for tab in HomeTab}
        known_options = {option.value for option in AssignmentOption}
        options = [AssignmentOption(v) for v in (self.assignment_options or []) if v in known_options]
        if not options:
            options = list(DEFAULT_ASSIGNMENT_OPTIONS)
        default = (
            AssignmentOption(self.default_assignment)
            if self.default_assignment in known_options
            else DEFAULT_ASSIGNMENT
        )
        return SystemRole(
            system=self.system,
            role_id=self.role_id,
            name=self.name,
            # Ação que saiu do catálogo deixa de valer, sem quebrar a leitura.
            actions=[Action(value) for value in self.actions if value in known],
            is_default=self.is_default,
            created_at=self.created_at,
            updated_at=self.updated_at,
            # Valor desconhecido (gravado por fora) volta para a lista, sem quebrar a leitura.
            home_tab=HomeTab(self.home_tab) if self.home_tab in known_tabs else HomeTab.LIST,
            assignment_options=options,
            default_assignment=default if default in options else options[0],
        )

    @staticmethod
    def build_pk(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def build_sk(role_id: str) -> str:
        return f"{SystemRoleDynamoDTO.SK_PREFIX}{role_id}"
