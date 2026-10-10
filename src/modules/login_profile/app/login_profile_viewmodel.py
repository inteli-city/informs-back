from .login_profile_usecase import LoginResult
from src.shared.helpers.contracts.endpoints.profile_contract import LoginProfileResponseSchema
from src.shared.helpers.viewmodels.profile_dict_builders import build_profile_dict, build_system_access_dict


class LoginProfileViewmodel:
    def __init__(self, result: LoginResult):
        self.result = result

    def to_dict(self) -> dict:
        payload = {
            **build_profile_dict(self.result.profile),
            "just_created": self.result.just_created,
            "systems": [build_system_access_dict(access) for access in self.result.systems],
        }
        return LoginProfileResponseSchema.model_validate(payload).model_dump()
