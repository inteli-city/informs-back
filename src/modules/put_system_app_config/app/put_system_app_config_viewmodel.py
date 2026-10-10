from src.shared.helpers.contracts.endpoints.app_config_admin_contract import PutSystemAppConfigResponseSchema
from .put_system_app_config_usecase import SystemAppConfigSaved


class PutSystemAppConfigViewmodel:
    def __init__(self, saved: SystemAppConfigSaved):
        self.saved = saved

    def to_dict(self):
        payload = {
            "system": self.saved.system,
            "values": self.saved.values,
            "version": self.saved.version,
            "effective": self.saved.effective.model_dump(),
        }
        return PutSystemAppConfigResponseSchema.model_validate(payload).model_dump()
