from typing import List

from .get_system_users_usecase import SystemUser
from src.shared.helpers.contracts.endpoints.system_access_contract import GetSystemUsersResponseSchema


class GetSystemUsersViewmodel:
    def __init__(self, system: str, users: List[SystemUser]):
        self.system = system
        self.users = users

    def to_dict(self) -> dict:
        payload = {
            "system": self.system,
            "users": [
                {
                    "user_id": user.membership.user_id,
                    "name": user.profile.name if user.profile else None,
                    "email": user.profile.email if user.profile else None,
                    "active": bool(user.profile and user.profile.active),
                    "role_id": user.membership.role_id,
                    "role_name": user.role_name,
                }
                for user in self.users
            ],
        }
        return GetSystemUsersResponseSchema.model_validate(payload).model_dump()
