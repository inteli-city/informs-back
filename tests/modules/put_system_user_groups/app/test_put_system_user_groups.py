import pytest

from src.modules.put_system_user.app.put_system_user_usecase import PutSystemUserUsecase
from src.modules.put_system_user_groups.app.put_system_user_groups_controller import PutSystemUserGroupsController
from src.modules.put_system_user_groups.app.put_system_user_groups_usecase import PutSystemUserGroupsUsecase
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    SUPER_ADMIN_ID,
    TECNICO_ROLE_ID,
    requester_user,
)
from tests.modules.group_fixtures import GROUP_A_ID, GROUP_B_ID, GROUPS_MANAGER_ID, GroupScenario


class TestPutSystemUserGroupsUsecase:
    def setup_method(self):
        self.scenario = GroupScenario()
        self.usecase = PutSystemUserGroupsUsecase(
            self.scenario.access_control, self.scenario.group_repo, self.scenario.profile_repo,
        )

    def test_users_manage_sets_groups(self):
        membership = self.usecase(MANAGER_ID, "GAIA", INSPECTOR_ID, [GROUP_A_ID, GROUP_B_ID])

        assert membership.groups == [GROUP_A_ID, GROUP_B_ID]
        assert self.scenario.access_control.groups_in(INSPECTOR_ID, "GAIA") == [GROUP_A_ID, GROUP_B_ID]

    def test_replaces_the_previous_list_and_keeps_the_role(self):
        self.usecase(ADMIN_ID, "GAIA", INSPECTOR_ID, [GROUP_A_ID])
        membership = self.usecase(ADMIN_ID, "GAIA", INSPECTOR_ID, [])

        assert membership.groups == []
        assert membership.role_id == TECNICO_ROLE_ID

    def test_unknown_group_is_rejected(self):
        with pytest.raises(EntityError):
            self.usecase(ADMIN_ID, "GAIA", INSPECTOR_ID, ["nao-existe"])

    def test_person_without_membership_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(SUPER_ADMIN_ID, "UBERLANDIA", INSPECTOR_ID, [])

    def test_groups_manage_alone_cannot_distribute_people(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(GROUPS_MANAGER_ID, "GAIA", INSPECTOR_ID, [GROUP_A_ID])

    def test_changing_the_role_keeps_the_groups(self):
        self.usecase(ADMIN_ID, "GAIA", INSPECTOR_ID, [GROUP_A_ID])
        put_role = PutSystemUserUsecase(
            self.scenario.access_control, self.scenario.profile_repo, self.scenario.role_repo,
        )

        put_role(ADMIN_ID, "GAIA", INSPECTOR_ID, GESTOR_ROLE_ID)

        assert self.scenario.access_control.groups_in(INSPECTOR_ID, "GAIA") == [GROUP_A_ID]


class TestPutSystemUserGroupsController:
    def setup_method(self):
        scenario = GroupScenario()
        self.controller = PutSystemUserGroupsController(PutSystemUserGroupsUsecase(
            scenario.access_control, scenario.group_repo, scenario.profile_repo,
        ))

    def _request(self, **body):
        return HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "user_id": INSPECTOR_ID, **body,
        })

    def test_returns_200(self):
        response = self.controller(self._request(groups=[GROUP_A_ID]))

        assert response.status_code == 200
        assert response.body == {"system": "GAIA", "user_id": INSPECTOR_ID, "groups": [GROUP_A_ID]}

    def test_unknown_group_returns_400(self):
        response = self.controller(self._request(groups=["nao-existe"]))
        assert response.status_code == 400

    def test_missing_groups_returns_400(self):
        response = self.controller(self._request())
        assert response.status_code == 400
