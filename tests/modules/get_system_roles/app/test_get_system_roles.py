from src.modules.get_system_roles.app.get_system_roles_controller import GetSystemRolesController
from src.modules.get_system_roles.app.get_system_roles_usecase import GetSystemRolesUsecase
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    AccessScenario,
    requester_user,
)


class TestGetSystemRoles:
    def setup_method(self):
        scenario = AccessScenario()
        self.controller = GetSystemRolesController(GetSystemRolesUsecase(scenario.access_control, scenario.role_repo))

    def _get(self, requester, system="GAIA"):
        return self.controller(HttpRequest(body={"requester_user": requester_user(requester), "system": system}))

    def test_lists_fixed_admin_first_then_roles_by_name(self):
        response = self._get(ADMIN_ID)

        assert response.status_code == 200
        names = [role["name"] for role in response.body["roles"]]
        assert names == ["Administrador", "Coordenador", "Gestor", "Técnico"]
        admin = response.body["roles"][0]
        assert admin["fixed"] is True
        assert admin["actions"] == [action.value for action in Action]

    def test_manager_with_users_manage_can_list(self):
        assert self._get(MANAGER_ID).status_code == 200

    def test_field_person_cannot_list(self):
        assert self._get(INSPECTOR_ID).status_code == 403

    def test_other_system_is_forbidden(self):
        assert self._get(ADMIN_ID, system="UBERLANDIA").status_code == 403
