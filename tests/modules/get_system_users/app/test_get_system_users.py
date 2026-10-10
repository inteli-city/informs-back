from src.modules.get_system_users.app.get_system_users_controller import GetSystemUsersController
from src.modules.get_system_users.app.get_system_users_usecase import GetSystemUsersUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


class TestGetSystemUsers:
    def setup_method(self):
        scenario = AccessScenario()
        self.controller = GetSystemUsersController(
            GetSystemUsersUsecase(scenario.access_control, scenario.profile_repo, scenario.role_repo)
        )

    def _get(self, requester, system="GAIA"):
        return self.controller(HttpRequest(body={"requester_user": requester_user(requester), "system": system}))

    def test_lists_people_by_name_with_their_role(self):
        response = self._get(MANAGER_ID)

        assert response.status_code == 200
        users = response.body["users"]
        assert [user["name"] for user in users] == ["Ana Admin", "Inspector Mock", "Maria Coordenadora"]
        inspector = next(user for user in users if user["user_id"] == INSPECTOR_ID)
        assert (inspector["role_id"], inspector["role_name"], inspector["active"]) == (TECNICO_ROLE_ID, "Técnico", True)
        admin = next(user for user in users if user["user_id"] == ADMIN_ID)
        assert admin["role_name"] == "Administrador"

    def test_without_users_manage_returns_403(self):
        assert self._get(INSPECTOR_ID).status_code == 403

    def test_other_system_returns_403(self):
        assert self._get(ADMIN_ID, system="UBERLANDIA").status_code == 403
