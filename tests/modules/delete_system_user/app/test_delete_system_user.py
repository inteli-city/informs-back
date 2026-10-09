import pytest

from src.modules.delete_system_user.app.delete_system_user_controller import DeleteSystemUserController
from src.modules.delete_system_user.app.delete_system_user_usecase import DeleteSystemUserUsecase
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    SUPER_ADMIN_ID,
    AccessScenario,
    requester_user,
)


class TestDeleteSystemUserUsecase:
    def setup_method(self):
        self.scenario = AccessScenario()
        self.usecase = DeleteSystemUserUsecase(self.scenario.access_control, self.scenario.profile_repo)

    def test_removes_the_membership(self):
        self.usecase(MANAGER_ID, "GAIA", INSPECTOR_ID)
        assert self.scenario.profile_repo.get_membership(INSPECTOR_ID, "GAIA") is None

    def test_only_super_admin_removes_an_admin(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", ADMIN_ID)

        self.usecase(SUPER_ADMIN_ID, "GAIA", ADMIN_ID)
        assert self.scenario.profile_repo.get_membership(ADMIN_ID, "GAIA") is None

    def test_manager_cannot_remove_someone_with_more_actions(self):
        self.scenario.join(INSPECTOR_ID, "GAIA", GESTOR_ROLE_ID)
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", INSPECTOR_ID)

    def test_without_membership_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", SUPER_ADMIN_ID)

    def test_without_users_manage_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", MANAGER_ID)


class TestDeleteSystemUserController:
    def test_returns_200_with_ids(self):
        scenario = AccessScenario()
        controller = DeleteSystemUserController(DeleteSystemUserUsecase(scenario.access_control, scenario.profile_repo))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "user_id": INSPECTOR_ID,
        }))

        assert response.status_code == 200
        assert response.body == {"system": "GAIA", "user_id": INSPECTOR_ID}

    def test_without_membership_returns_404(self):
        scenario = AccessScenario()
        controller = DeleteSystemUserController(DeleteSystemUserUsecase(scenario.access_control, scenario.profile_repo))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "user_id": SUPER_ADMIN_ID,
        }))

        assert response.status_code == 404
