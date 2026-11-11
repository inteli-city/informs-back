from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.helpers.contracts.endpoints.system_access_contract import PutSystemUserGroupsResponseSchema


class PutSystemUserGroupsViewmodel:
    def __init__(self, membership: SystemMembership):
        self.membership = membership

    def to_dict(self) -> dict:
        payload = {
            "system": self.membership.system,
            "user_id": self.membership.user_id,
            "groups": self.membership.groups,
        }
        return PutSystemUserGroupsResponseSchema.model_validate(payload).model_dump()
