from src.shared.domain.entities.profile import Profile
from src.shared.helpers.contracts.endpoints.profile_contract import UpdateProfileResponseSchema


class UpdateProfileViewmodel:
    def __init__(self, profile: Profile):
        self.profile = profile

    def to_dict(self) -> dict:
        payload = {
            "user_id": self.profile.user_id,
            "role": self.profile.role.value,
            "name": self.profile.name,
            "email": self.profile.email,
            "system": self.profile.system,
            "vehicle_plate": self.profile.vehicle_plate,
            "active": self.profile.active,
            "created_at": self.profile.created_at,
            "updated_at": self.profile.updated_at,
            "scope": self.profile.scope,
        }
        return UpdateProfileResponseSchema.model_validate(payload).model_dump()
