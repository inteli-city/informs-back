from src.shared.domain.entities.profile import Profile
from src.shared.helpers.contracts.endpoints.profile_contract import CreateProfileResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_profile_dict


class CreateProfileViewmodel:
    def __init__(self, profile: Profile):
        self.profile = profile

    def to_dict(self) -> dict:
        return CreateProfileResponseSchema.model_validate(build_profile_dict(self.profile)).model_dump()
