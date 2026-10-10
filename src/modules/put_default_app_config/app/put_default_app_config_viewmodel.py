from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.helpers.contracts.endpoints.app_config_admin_contract import PutDefaultAppConfigResponseSchema


class PutDefaultAppConfigViewmodel:
    def __init__(self, config: DefaultAppConfig):
        self.config = config

    def to_dict(self):
        payload = {"values": self.config.values, "version": self.config.version}
        return PutDefaultAppConfigResponseSchema.model_validate(payload).model_dump()
