from .get_app_config_usecase import AppConfigResult
from src.shared.helpers.contracts.endpoints.get_app_config_contract import GetAppConfigResponseSchema


class GetAppConfigViewmodel:
    result: AppConfigResult

    def __init__(self, result: AppConfigResult):
        self.result = result

    def to_dict(self):
        payload = {
            "default": {
                "version": self.result.default.version,
                "config": self.result.default.config.model_dump(),
            },
            "systems": [
                {"system": item.system, "version": item.version, "config": item.config.model_dump()}
                for item in self.result.systems
            ],
        }
        return GetAppConfigResponseSchema.model_validate(payload).model_dump()
