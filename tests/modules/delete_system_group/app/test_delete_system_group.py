import pytest

from src.modules.delete_system_group.app.delete_system_group_controller import DeleteSystemGroupController
from src.modules.delete_system_group.app.delete_system_group_usecase import DeleteSystemGroupUsecase
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import ADMIN_ID, INSPECTOR_ID, MANAGER_ID, requester_user
from tests.modules.group_fixtures import GROUP_A_ID, GROUP_B_ID, GroupScenario
from tests.modules.test_groups_scenario import _form


class TestDeleteSystemGroupUsecase:
    def setup_method(self):
        self.scenario = GroupScenario()
        self.usecase = DeleteSystemGroupUsecase(
            self.scenario.access_control, self.scenario.group_repo, self.scenario.profile_repo, self.scenario.form_repo,
        )

    def test_deletes_unused_group(self):
        self.usecase(ADMIN_ID, "GAIA", GROUP_B_ID)
        assert self.scenario.group_repo.get_group("GAIA", GROUP_B_ID) is None

    def test_group_with_people_is_a_conflict(self):
        self.scenario.set_groups(MANAGER_ID, "GAIA", [GROUP_A_ID])
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID)

    def test_group_with_open_form_is_a_conflict(self):
        form = _form("20000000-0000-4000-8000-000000000001", groups=[GROUP_A_ID])
        form.system = "GAIA"
        self.scenario.form_repo.forms.append(form)

        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", GROUP_A_ID)

    def test_unknown_group_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", "nao-existe")

    def test_without_permission_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", GROUP_B_ID)


class TestDeleteSystemGroupController:
    def test_returns_200(self):
        scenario = GroupScenario()
        controller = DeleteSystemGroupController(DeleteSystemGroupUsecase(
            scenario.access_control, scenario.group_repo, scenario.profile_repo, scenario.form_repo,
        ))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "group_id": GROUP_B_ID,
        }))

        assert response.status_code == 200
        assert response.body == {"system": "GAIA", "group_id": GROUP_B_ID}
