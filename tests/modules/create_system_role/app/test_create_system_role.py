import pytest

from src.modules.create_system_role.app.create_system_role_controller import CreateSystemRoleController
from src.modules.create_system_role.app.create_system_role_usecase import CreateSystemRoleUsecase
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


class TestCreateSystemRoleUsecase:
    def setup_method(self):
        self.scenario = AccessScenario()
        self.usecase = CreateSystemRoleUsecase(self.scenario.access_control, self.scenario.role_repo)

    def test_system_admin_creates_role_with_any_action(self):
        role = self.usecase(ADMIN_ID, "GAIA", "Fiscal", [Action.FORMS_VIEW_ALL, Action.FORMS_ASSIGN], False)

        assert role.name == "Fiscal"
        assert self.scenario.role_repo.get_role("GAIA", role.role_id) is not None

    def test_manager_creates_role_with_actions_they_have(self):
        role = self.usecase(MANAGER_ID, "GAIA", "Campo", [Action.TRACKING_START], False)
        assert role.actions == [Action.TRACKING_START]

    def test_manager_cannot_grant_actions_they_do_not_have(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", "Gestão", [Action.FORMS_ASSIGN], False)

    def test_without_roles_manage_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", "Campo", [], False)

    def test_manage_in_another_system_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(ADMIN_ID, "UBERLANDIA", "Campo", [], False)

    def test_duplicated_name_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", "técnico", [], False)

    def test_new_default_role_takes_the_mark_from_the_old_one(self):
        role = self.usecase(ADMIN_ID, "GAIA", "Novo padrão", [Action.TRACKING_START], True)

        assert self.scenario.role_repo.get_role("GAIA", role.role_id).is_default is True
        assert self.scenario.role_repo.get_role("GAIA", TECNICO_ROLE_ID).is_default is False


class TestCreateSystemRoleController:
    def setup_method(self):
        scenario = AccessScenario()
        self.controller = CreateSystemRoleController(CreateSystemRoleUsecase(scenario.access_control, scenario.role_repo))

    def _request(self, requester, **body):
        return HttpRequest(body={"requester_user": requester_user(requester), "system": "GAIA", **body})

    def test_returns_201(self):
        response = self.controller(self._request(ADMIN_ID, name="Fiscal", actions=["forms.view_all"]))

        assert response.status_code == 201
        assert response.body["name"] == "Fiscal"
        assert response.body["actions"] == ["forms.view_all"]
        assert response.body["fixed"] is False

    def test_unknown_action_returns_400(self):
        response = self.controller(self._request(ADMIN_ID, name="Fiscal", actions=["forms.delete_everything"]))
        assert response.status_code == 400

    def test_reserved_admin_name_returns_400(self):
        response = self.controller(self._request(ADMIN_ID, name="Administrador", actions=[]))
        assert response.status_code == 400

    def test_without_permission_returns_403(self):
        response = self.controller(self._request(INSPECTOR_ID, name="Fiscal", actions=[]))
        assert response.status_code == 403

    def test_duplicated_name_returns_409(self):
        response = self.controller(self._request(ADMIN_ID, name="Técnico", actions=[]))
        assert response.status_code == 409
