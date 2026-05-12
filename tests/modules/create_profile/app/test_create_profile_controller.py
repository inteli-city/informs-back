import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_profile.app.create_profile_controller import CreateProfileController
from src.modules.create_profile.app.create_profile_usecase import CreateProfileUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"   # ADMIN no mock
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"  # INSPECTOR no mock
NEW_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120099"


def _payload(sub: str = ADMIN_USER_ID, groups: str = "FORMULARIOS,GAIA"):
    return {
        "sub": sub,
        "name": "Tester",
        "email": "tester@example.com",
        "cognito:groups": groups,
    }


def _body(requester_sub=ADMIN_USER_ID, **overrides):
    body = {
        "requester_user": _payload(sub=requester_sub),
        "user_id": NEW_USER_ID,
        "role": "INSPECTOR",
        "name": "New Inspector",
        "email": "new@example.com",
        "system": "GAIA",
    }
    body.update(overrides)
    return body


class TestCreateProfileController:
    def setup_method(self):
        self.repo = ProfileRepositoryMock()
        self.usecase = CreateProfileUsecase(self.repo)
        self.controller = CreateProfileController(self.usecase)

    def test_admin_creates_inspector_returns_201(self):
        response = self.controller(HttpRequest(body=_body()))
        assert response.status_code == 201
        assert response.body["user_id"] == NEW_USER_ID
        assert response.body["role"] == "INSPECTOR"
        assert response.body["active"] is True

    def test_admin_creates_admin_returns_201(self):
        response = self.controller(HttpRequest(body=_body(role="ADMIN")))
        assert response.status_code == 201
        assert response.body["role"] == "ADMIN"

    def test_inspector_cannot_create_returns_403(self):
        response = self.controller(HttpRequest(body=_body(requester_sub=INSPECTOR_USER_ID)))
        assert response.status_code == 403

    def test_unknown_requester_returns_403(self):
        response = self.controller(
            HttpRequest(body=_body(requester_sub="00000000-0000-0000-0000-000000000000"))
        )
        assert response.status_code == 403

    def test_duplicate_user_id_returns_409(self):
        # tenta criar um perfil com o user_id de quem já existe
        response = self.controller(HttpRequest(body=_body(user_id=INSPECTOR_USER_ID)))
        assert response.status_code == 409

    def test_invalid_role_returns_400(self):
        response = self.controller(HttpRequest(body=_body(role="SUPERADMIN")))
        assert response.status_code == 400

    def test_invalid_email_returns_400(self):
        response = self.controller(HttpRequest(body=_body(email="not-an-email")))
        assert response.status_code == 400

    def test_short_user_id_returns_400(self):
        response = self.controller(HttpRequest(body=_body(user_id="too-short")))
        assert response.status_code == 400

    def test_missing_requester_returns_400(self):
        body = _body()
        del body["requester_user"]
        response = self.controller(HttpRequest(body=body))
        assert response.status_code == 400

    def test_user_without_formularios_group_returns_403(self):
        body = _body()
        body["requester_user"]["cognito:groups"] = "SGC,GAIA"  # sem FORMULARIOS
        response = self.controller(HttpRequest(body=body))
        assert response.status_code == 403
