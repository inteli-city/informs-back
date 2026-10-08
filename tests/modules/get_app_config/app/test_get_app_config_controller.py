import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_app_config.app.get_app_config_controller import GetAppConfigController
from src.modules.get_app_config.app.get_app_config_usecase import GetAppConfigUsecase
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock


def _requester(groups="FORMULARIOS,UBERLANDIA"):
    return {"sub": "user-123", "name": "User", "email": "user@test.com", "cognito:groups": groups}


class TestGetAppConfigController:
    def setup_method(self):
        self.repo = SystemConfigRepositoryMock()
        self.repo.put(SystemConfig(
            system="UBERLANDIA", created_at=1, updated_at=1,
            app_config={"flows": {"cancel_form": True}}, app_config_version=1,
        ))
        self.controller = GetAppConfigController(GetAppConfigUsecase(self.repo))

    def test_success(self):
        response = self.controller(HttpRequest(body={"requester_user": _requester()}))

        assert response.status_code == 200
        assert response.body["default"]["version"] == "0"
        assert response.body["default"]["config"]["flows"]["cancel_form"] is False
        assert response.body["systems"][0]["system"] == "UBERLANDIA"
        assert response.body["systems"][0]["version"] == "0.1"
        assert response.body["systems"][0]["config"]["flows"]["cancel_form"] is True

    def test_missing_requester(self):
        response = self.controller(HttpRequest(body={}))
        assert response.status_code == 400

    def test_user_outside_formularios_group(self):
        response = self.controller(HttpRequest(body={"requester_user": _requester("UBERLANDIA")}))
        assert response.status_code == 403
