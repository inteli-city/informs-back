from .put_system_user_usecase import SystemUserSaved
from src.shared.helpers.contracts.endpoints.system_access_contract import PutSystemUserResponseSchema


class PutSystemUserViewmodel:
    def __init__(self, saved: SystemUserSaved):
        self.saved = saved

    def to_dict(self) -> dict:
        payload = {
            "system": self.saved.membership.system,
            "user_id": self.saved.membership.user_id,
            "role_id": self.saved.membership.role_id,
            "role_name": self.saved.role_name,
        }
        return PutSystemUserResponseSchema.model_validate(payload).model_dump()
