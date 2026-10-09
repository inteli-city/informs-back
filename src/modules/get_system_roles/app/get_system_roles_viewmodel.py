from typing import List

from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, ADMIN_ROLE_NAME, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.contracts.endpoints.system_access_contract import GetSystemRolesResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_system_role_dict


class GetSystemRolesViewmodel:
    def __init__(self, system: str, roles: List[SystemRole]):
        self.system = system
        self.roles = roles

    def to_dict(self) -> dict:
        # O ADMIN fixo vem primeiro: a tela de roles mostra, mas não edita.
        admin = {
            "system": self.system,
            "role_id": ADMIN_ROLE_ID,
            "name": ADMIN_ROLE_NAME,
            "actions": [action.value for action in Action],
            "is_default": False,
            "fixed": True,
        }
        payload = {"system": self.system, "roles": [admin, *(build_system_role_dict(role) for role in self.roles)]}
        return GetSystemRolesResponseSchema.model_validate(payload).model_dump()
