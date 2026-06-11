from src.shared.domain.entities.profile import Profile
from src.shared.helpers.contracts.endpoints.profile_contract import DeleteProfileResponseSchema


class DeleteProfileViewmodel:
    def __init__(self, profile: Profile):
        self.profile = profile

    def to_dict(self) -> dict:
        payload = {
            "user_id": self.profile.user_id,
            "active": self.profile.active,
            "updated_at": self.profile.updated_at,
        }
        return DeleteProfileResponseSchema.model_validate(payload).model_dump()
