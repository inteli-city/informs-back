import os
import sys

sys.path.append(os.getcwd())

from src.modules.update_profile.app.update_profile_controller import UpdateProfileController
from src.modules.update_profile.app.update_profile_usecase import UpdateProfileUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


def _payload(sub: str = ADMIN_USER_ID, groups: str = "FORMULARIOS,GAIA"):
    return {
        "sub": sub,
        "name": "Tester",
        "email": "tester@example.com",
        "cognito:groups": groups,
    }


def _request(target_user_id: str, role: str, scope=None, requester_sub: str = ADMIN_USER_ID):
    return HttpRequest(body={
        "requester_user": _payload(sub=requester_sub),
        "user_id": target_user_id,
        "role": role,
        "scope": scope if scope is not None else {},
    })


class TestUpdateProfileController:
    def setup_method(self):
        self.repo = ProfileRepositoryMock()
        self.usecase = UpdateProfileUsecase(self.repo)
        self.controller = UpdateProfileController(self.usecase)

    def test_admin_updates_inspector_returns_200(self):
        response = self.controller(_request(
            target_user_id=INSPECTOR_USER_ID, role="MANAGER", scope={"bairro": ["Santa Mônica"]},
        ))
        assert response.status_code == 200
        assert response.body["role"] == "MANAGER"
        assert response.body["scope"] == {"bairro": ["Santa Mônica"]}

    def test_invalid_role_returns_400(self):
        response = self.controller(_request(target_user_id=INSPECTOR_USER_ID, role="NOT_A_ROLE"))
        assert response.status_code == 400

    def test_inspector_cannot_update_returns_403(self):
        response = self.controller(_request(
            target_user_id=ADMIN_USER_ID, role="MANAGER", requester_sub=INSPECTOR_USER_ID,
        ))
        assert response.status_code == 403

    def test_target_not_found_returns_404(self):
        response = self.controller(_request(
            target_user_id="00000000-0000-0000-0000-000000000000", role="MANAGER",
        ))
        assert response.status_code == 404
