import pytest

from src.modules.delete_system_role.app.delete_system_role_controller import DeleteSystemRoleController
from src.modules.delete_system_role.app.delete_system_role_usecase import DeleteSystemRoleUsecase
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    INSPECTOR_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


class TestDeleteSystemRoleUsecase:
    def setup_method(self):
        self.scenario = AccessScenario()
        self.usecase = DeleteSystemRoleUsecase(
            self.scenario.access_control, self.scenario.role_repo, self.scenario.profile_repo,
        )

    def test_deletes_unused_role(self):
        self.usecase(ADMIN_ID, "GAIA", GESTOR_ROLE_ID)
        assert self.scenario.role_repo.get_role("GAIA", GESTOR_ROLE_ID) is None

    def test_role_in_use_is_a_conflict(self):
        self.scenario.role_repo.put_role(SystemRole(
            system="GAIA", role_id="r-usado", name="Usado", actions=[Action.TRACKING_START], created_at=1, updated_at=1,
        ))
        self.scenario.join(INSPECTOR_ID, "GAIA", "r-usado")

        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", "r-usado")

    def test_default_role_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", TECNICO_ROLE_ID)

    def test_admin_role_is_fixed(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(ADMIN_ID, "GAIA", ADMIN_ROLE_ID)

    def test_unknown_role_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", "r-nao-existe")

    def test_without_roles_manage_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", GESTOR_ROLE_ID)


class TestDeleteSystemRoleController:
    def test_returns_200_with_ids(self):
        scenario = AccessScenario()
        controller = DeleteSystemRoleController(
            DeleteSystemRoleUsecase(scenario.access_control, scenario.role_repo, scenario.profile_repo)
        )

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "role_id": GESTOR_ROLE_ID,
        }))

        assert response.status_code == 200
        assert response.body == {"system": "GAIA", "role_id": GESTOR_ROLE_ID}

    def test_default_role_returns_409(self):
        scenario = AccessScenario()
        controller = DeleteSystemRoleController(
            DeleteSystemRoleUsecase(scenario.access_control, scenario.role_repo, scenario.profile_repo)
        )

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "role_id": TECNICO_ROLE_ID,
        }))

        assert response.status_code == 409
