import pytest

from src.modules.create_system_group.app.create_system_group_controller import CreateSystemGroupController
from src.modules.create_system_group.app.create_system_group_usecase import CreateSystemGroupUsecase
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import ADMIN_ID, MANAGER_ID, requester_user
from tests.modules.group_fixtures import GROUP_A_ID, GROUPS_MANAGER_ID, GroupScenario


class TestCreateSystemGroupUsecase:
    def setup_method(self):
        self.scenario = GroupScenario()
        self.usecase = CreateSystemGroupUsecase(self.scenario.access_control, self.scenario.group_repo)

    def test_groups_manage_creates_group(self):
        group = self.usecase(GROUPS_MANAGER_ID, "GAIA", "equipe-leste", "Equipe Leste")

        assert group.group_id == "equipe-leste"
        assert self.scenario.group_repo.get_group("GAIA", "equipe-leste").name == "Equipe Leste"

    def test_users_manage_alone_cannot_create(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", "equipe-leste", "Equipe Leste")

    def test_duplicated_id_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID, "Outra")

    def test_duplicated_name_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", "equipe-c", "equipe a")


class TestCreateSystemGroupController:
    def setup_method(self):
        scenario = GroupScenario()
        self.controller = CreateSystemGroupController(
            CreateSystemGroupUsecase(scenario.access_control, scenario.group_repo)
        )

    def _request(self, requester, **body):
        return HttpRequest(body={"requester_user": requester_user(requester), "system": "GAIA", **body})

    def test_returns_201(self):
        response = self.controller(self._request(ADMIN_ID, group_id="equipe-leste", name="Equipe Leste"))

        assert response.status_code == 201
        assert response.body == {"system": "GAIA", "group_id": "equipe-leste", "name": "Equipe Leste"}

    @pytest.mark.parametrize("group_id", ["Equipe Leste", "equipe_leste", "-leste", "", "a" * 41])
    def test_invalid_id_returns_400(self, group_id):
        response = self.controller(self._request(ADMIN_ID, group_id=group_id, name="Equipe"))
        assert response.status_code == 400

    def test_duplicated_returns_409(self):
        response = self.controller(self._request(ADMIN_ID, group_id=GROUP_A_ID, name="Outra"))
        assert response.status_code == 409
