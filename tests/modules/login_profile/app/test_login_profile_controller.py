import os
import sys

sys.path.append(os.getcwd())

from src.modules.login_profile.app.login_profile_controller import LoginProfileController
from src.modules.login_profile.app.login_profile_usecase import LoginProfileUsecase
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import (
    MOCK_TECNICO_ROLE_ID,
    SystemRoleRepositoryMock,
)


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
NEW_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120099"
ALL_ACTIONS = sorted(action.value for action in Action)


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
        self.role_repo = SystemRoleRepositoryMock()
        self.usecase = LoginProfileUsecase(self.repo, self.role_repo)
        self.controller = LoginProfileController(self.usecase)

    def _login(self, **kwargs):
        return self.controller(HttpRequest(body={"requester_user": _payload(**kwargs)}))

    def test_super_admin_gets_every_action_in_each_system(self):
        response = self._login(sub=ADMIN_USER_ID)

        assert response.status_code == 200
        assert response.body["just_created"] is False
        assert response.body["super_admin"] is True
        assert response.body["user_id"] == ADMIN_USER_ID
        # Também ganha o role padrão do sistema, mas como super admin tem todas as ações.
        assert response.body["systems"] == [
            {"system": "GAIA", "role_id": MOCK_TECNICO_ROLE_ID, "role_name": "Técnico", "actions": ALL_ACTIONS},
        ]

    def test_existing_person_gets_the_actions_of_their_role(self):
        response = self._login(sub=INSPECTOR_USER_ID)

        assert response.status_code == 200
        assert response.body["just_created"] is False
        assert response.body["super_admin"] is False
        assert response.body["systems"] == [
            {"system": "GAIA", "role_id": MOCK_TECNICO_ROLE_ID, "role_name": "Técnico", "actions": ["tracking.start"]},
        ]

    def test_first_login_creates_profile_and_joins_with_default_role(self):
        response = self._login(sub=NEW_USER_ID, name="Brand New", email="new@example.com")

        assert response.status_code == 200
        assert response.body["just_created"] is True
        assert response.body["active"] is True
        assert response.body["super_admin"] is False
        assert response.body["systems"][0]["role_id"] == MOCK_TECNICO_ROLE_ID
        assert self.repo.get_by_user_id(NEW_USER_ID) is not None
        assert self.repo.get_membership(NEW_USER_ID, "GAIA").role_id == MOCK_TECNICO_ROLE_ID

    def test_system_without_default_role_has_no_actions(self):
        response = self._login(sub=NEW_USER_ID, groups="FORMULARIOS,SGC")

        assert response.status_code == 200
        assert response.body["systems"] == [{"system": "SGC", "role_id": None, "role_name": None, "actions": []}]
        assert self.repo.get_membership(NEW_USER_ID, "SGC") is None

    def test_new_cognito_group_joins_existing_person_with_default_role(self):
        response = self._login(sub=INSPECTOR_USER_ID, groups="FORMULARIOS,GAIA,SGC")

        assert [item["system"] for item in response.body["systems"]] == ["GAIA", "SGC"]
        assert self.repo.get_membership(INSPECTOR_USER_ID, "GAIA").role_id == MOCK_TECNICO_ROLE_ID

    def test_inactive_profile_returns_403(self):
        self.repo.soft_delete(user_id=ADMIN_USER_ID, updated_at=1)

        assert self._login(sub=ADMIN_USER_ID).status_code == 403

    def test_user_without_extra_system_group_returns_403(self):
        # Cognito grupos = só FORMULARIOS — sem nenhum system real
        assert self._login(sub=NEW_USER_ID, groups="FORMULARIOS").status_code == 403

    def test_user_without_formularios_group_returns_403(self):
        assert self._login(sub=NEW_USER_ID, groups="GAIA,SGC").status_code == 403

    def test_missing_requester_returns_400(self):
        response = self.controller(HttpRequest(body={}))
        assert response.status_code == 400
