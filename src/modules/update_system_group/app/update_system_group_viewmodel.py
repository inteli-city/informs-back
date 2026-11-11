from src.shared.domain.entities.system_group import SystemGroup
from src.shared.helpers.contracts.endpoints.system_access_contract import SystemGroupResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_system_group_dict


class UpdateSystemGroupViewmodel:
    def __init__(self, group: SystemGroup):
        self.group = group

    def to_dict(self) -> dict:
        return SystemGroupResponseSchema.model_validate(build_system_group_dict(self.group)).model_dump()
