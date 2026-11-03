import pytest

from src.modules.update_system_group.app.update_system_group_controller import UpdateSystemGroupController
from src.modules.update_system_group.app.update_system_group_usecase import UpdateSystemGroupUsecase
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import ADMIN_ID, INSPECTOR_ID, requester_user
from tests.modules.group_fixtures import GROUP_A_ID, GroupScenario


class TestUpdateSystemGroupUsecase:
    def setup_method(self):
        self.scenario = GroupScenario()
        self.usecase = UpdateSystemGroupUsecase(self.scenario.access_control, self.scenario.group_repo)

    def test_renames_and_keeps_the_id(self):
        group = self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID, "Equipe Norte")

        assert group.group_id == GROUP_A_ID
        assert self.scenario.group_repo.get_group("GAIA", GROUP_A_ID).name == "Equipe Norte"

    def test_unknown_group_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", "nao-existe", "Nome")

    def test_name_of_another_group_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID, "Equipe B")

    def test_same_name_is_not_a_conflict(self):
        assert self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID, "Equipe A").name == "Equipe A"

    def test_without_permission_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", GROUP_A_ID, "Nome")


class TestUpdateSystemGroupController:
    def test_returns_200(self):
        scenario = GroupScenario()
        controller = UpdateSystemGroupController(UpdateSystemGroupUsecase(scenario.access_control, scenario.group_repo))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "group_id": GROUP_A_ID, "name": "Norte",
        }))

        assert response.status_code == 200
        assert response.body["name"] == "Norte"
