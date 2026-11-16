from .get_system_assignees_usecase import SystemAssignees
from src.shared.helpers.contracts.endpoints.system_access_contract import GetSystemAssigneesResponseSchema


class GetSystemAssigneesViewmodel:
    def __init__(self, system: str, assignees: SystemAssignees):
        self.system = system
        self.assignees = assignees

    def to_dict(self) -> dict:
        payload = {
            "system": self.system,
            "allows_group_only": self.assignees.allows_group_only,
            "groups": [{"group_id": group.group_id, "name": group.name} for group in self.assignees.groups],
            "users": [
                {
                    "user_id": user.membership.user_id,
                    "name": user.profile.name,
                    "groups": user.membership.groups,
                }
                for user in self.assignees.users
            ],
        }
        return GetSystemAssigneesResponseSchema.model_validate(payload).model_dump()
