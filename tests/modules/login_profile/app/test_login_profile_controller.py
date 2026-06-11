import os
import sys

sys.path.append(os.getcwd())

from src.modules.login_profile.app.login_profile_controller import LoginProfileController
from src.modules.login_profile.app.login_profile_usecase import LoginProfileUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
NEW_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120099"


def _payload(sub: str, name: str = "Tester", email: str = "tester@example.com",
             groups: str = "FORMULARIOS,GAIA"):
    return {
        "sub": sub,
        "name": name,
        "email": email,
        "cognito:groups": groups,
    }


class TestLoginProfileController:
    def setup_method(self):
        self.repo = ProfileRepositoryMock()
        self.usecase = LoginProfileUsecase(self.repo)
        self.controller = LoginProfileController(self.usecase)

    def test_existing_active_admin_returns_200_just_created_false(self):
        request = HttpRequest(body={"requester_user": _payload(sub=ADMIN_USER_ID)})
        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["just_created"] is False
        assert response.body["role"] == "ADMIN"
        assert response.body["user_id"] == ADMIN_USER_ID

    def test_existing_active_inspector_returns_200(self):
        request = HttpRequest(body={"requester_user": _payload(sub=INSPECTOR_USER_ID)})
        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["just_created"] is False
        assert response.body["role"] == "INSPECTOR"

    def test_first_login_auto_creates_inspector_returns_200(self):
        request = HttpRequest(body={"requester_user": _payload(
            sub=NEW_USER_ID, name="Brand New", email="new@example.com",
            groups="FORMULARIOS,GAIA",
        )})
        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["just_created"] is True
        assert response.body["role"] == "INSPECTOR"
        assert response.body["system"] == "GAIA"
        assert response.body["active"] is True
        # Persistido no repo
        assert self.repo.get_by_user_id(NEW_USER_ID) is not None

    def test_inactive_profile_returns_403(self):
        # desativa o admin do mock
        self.repo.soft_delete(user_id=ADMIN_USER_ID, updated_at=1)
        request = HttpRequest(body={"requester_user": _payload(sub=ADMIN_USER_ID)})
        response = self.controller(request)
        assert response.status_code == 403

    def test_user_without_extra_system_group_returns_403(self):
        # Cognito grupos = só FORMULARIOS — sem nenhum system real
        request = HttpRequest(body={"requester_user": _payload(
            sub=NEW_USER_ID, groups="FORMULARIOS",
        )})
        response = self.controller(request)
        assert response.status_code == 403

    def test_user_without_formularios_group_returns_403(self):
        request = HttpRequest(body={"requester_user": _payload(
            sub=NEW_USER_ID, groups="GAIA,SGC",
        )})
        response = self.controller(request)
        assert response.status_code == 403

    def test_missing_requester_returns_400(self):
        response = self.controller(HttpRequest(body={}))
        assert response.status_code == 400

    def test_first_login_picks_first_non_formularios_group_as_system(self):
        request = HttpRequest(body={"requester_user": _payload(
            sub=NEW_USER_ID, groups="FORMULARIOS,SGC,GAIA,INTELIFLEETS",
        )})
        response = self.controller(request)
        assert response.status_code == 200
        assert response.body["system"] == "SGC"
