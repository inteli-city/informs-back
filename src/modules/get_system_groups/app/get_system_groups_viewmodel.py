from typing import List

from src.shared.domain.entities.system_group import SystemGroup
from src.shared.helpers.contracts.endpoints.system_access_contract import GetSystemGroupsResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_system_group_dict


class GetSystemGroupsViewmodel:
    def __init__(self, system: str, groups: List[SystemGroup]):
        self.system = system
        self.groups = groups

    def to_dict(self) -> dict:
        payload = {"system": self.system, "groups": [build_system_group_dict(group) for group in self.groups]}
        return GetSystemGroupsResponseSchema.model_validate(payload).model_dump()
