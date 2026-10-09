from src.shared.domain.entities.system_role import SystemRole
from src.shared.helpers.contracts.endpoints.system_access_contract import SystemRoleResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_system_role_dict


class UpdateSystemRoleViewmodel:
    def __init__(self, role: SystemRole):
        self.role = role

    def to_dict(self) -> dict:
        return SystemRoleResponseSchema.model_validate(build_system_role_dict(self.role)).model_dump()
