from src.shared.domain.entities.app_config import AppConfig
from src.shared.helpers.contracts.endpoints.app_config_admin_contract import GetAppConfigAdminResponseSchema
from .get_app_config_admin_usecase import AppConfigAdminResult


class GetAppConfigAdminViewmodel:
    def __init__(self, result: AppConfigAdminResult):
        self.result = result

    def to_dict(self):
        payload = {
            "config_schema": AppConfig.model_json_schema(),
            "schema_defaults": AppConfig().model_dump(),
            "default_layer": {
                "values": self.result.default_layer.values,
                "version": self.result.default_layer.version,
            },
            "can_edit_default": self.result.can_edit_default,
            "systems": [
                {
                    "system": item.system,
                    "values": item.values,
                    "version": item.version,
                    "effective": item.effective.model_dump(),
                }
                for item in self.result.systems
            ],
        }
        return GetAppConfigAdminResponseSchema.model_validate(payload).model_dump()
