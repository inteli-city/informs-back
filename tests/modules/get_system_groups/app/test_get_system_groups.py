import pytest

from src.modules.get_system_groups.app.get_system_groups_controller import GetSystemGroupsController
from src.modules.get_system_groups.app.get_system_groups_usecase import GetSystemGroupsUsecase
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import ADMIN_ID, INSPECTOR_ID, MANAGER_ID, requester_user
from tests.modules.group_fixtures import GROUPS_MANAGER_ID, GroupScenario


class TestGetSystemGroupsUsecase:
    def setup_method(self):
        self.scenario = GroupScenario()
        self.usecase = GetSystemGroupsUsecase(self.scenario.access_control, self.scenario.group_repo)

    def test_lists_groups_sorted_by_name(self):
        groups = self.usecase(ADMIN_ID, "GAIA")
        assert [group.name for group in groups] == ["Equipe A", "Equipe B"]

    def test_groups_manage_can_list(self):
        assert len(self.usecase(GROUPS_MANAGER_ID, "GAIA")) == 2

    def test_users_manage_can_list_to_distribute_people(self):
        assert len(self.usecase(MANAGER_ID, "GAIA")) == 2

    def test_without_either_action_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA")


class TestGetSystemGroupsController:
    def setup_method(self):
        scenario = GroupScenario()
        self.controller = GetSystemGroupsController(GetSystemGroupsUsecase(scenario.access_control, scenario.group_repo))

    def test_returns_200(self):
        response = self.controller(HttpRequest(body={"requester_user": requester_user(ADMIN_ID), "system": "GAIA"}))

        assert response.status_code == 200
        assert response.body["system"] == "GAIA"
        assert response.body["groups"][0] == {"system": "GAIA", "group_id": "equipe-a", "name": "Equipe A"}

    def test_without_permission_returns_403(self):
        response = self.controller(HttpRequest(body={"requester_user": requester_user(INSPECTOR_ID), "system": "GAIA"}))
        assert response.status_code == 403
