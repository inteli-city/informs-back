import pytest

from src.modules.update_system_role.app.update_system_role_controller import UpdateSystemRoleController
from src.modules.update_system_role.app.update_system_role_usecase import UpdateSystemRoleUsecase
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    MANAGER_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


class TestUpdateSystemRoleUsecase:
    def setup_method(self):
        self.scenario = AccessScenario()
        self.usecase = UpdateSystemRoleUsecase(self.scenario.access_control, self.scenario.role_repo)

    def test_replaces_name_actions_and_keeps_created_at(self):
        role = self.usecase(ADMIN_ID, "GAIA", TECNICO_ROLE_ID, "Técnico de campo", [Action.TRACKING_START, Action.FORMS_RELEASE], True)

        assert role.name == "Técnico de campo"
        assert role.actions == [Action.TRACKING_START, Action.FORMS_RELEASE]
        assert role.created_at == 946684800000

    def test_admin_role_is_fixed(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(ADMIN_ID, "GAIA", ADMIN_ROLE_ID, "Chefe", [], False)

    def test_unknown_role_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", "r-nao-existe", "X", [], False)

    def test_manager_cannot_edit_role_with_actions_they_do_not_have(self):
        # O Gestor tem forms.assign, que o Coordenador (MANAGER_ID) não tem.
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", GESTOR_ROLE_ID, "Gestor", [], False)

    def test_manager_edits_role_within_their_actions(self):
        role = self.usecase(MANAGER_ID, "GAIA", TECNICO_ROLE_ID, "Técnico", [Action.TRACKING_START], True)
        assert role.actions == [Action.TRACKING_START]

    def test_name_of_another_role_is_a_conflict(self):
        with pytest.raises(DuplicatedItem):
            self.usecase(ADMIN_ID, "GAIA", TECNICO_ROLE_ID, "Gestor", [], False)

    def test_marking_default_unmarks_the_previous_one(self):
        self.usecase(ADMIN_ID, "GAIA", GESTOR_ROLE_ID, "Gestor", [Action.FORMS_ASSIGN], True)

        assert self.scenario.role_repo.get_role("GAIA", GESTOR_ROLE_ID).is_default is True
        assert self.scenario.role_repo.get_role("GAIA", TECNICO_ROLE_ID).is_default is False


class TestUpdateSystemRoleController:
    def test_returns_200(self):
        scenario = AccessScenario()
        controller = UpdateSystemRoleController(UpdateSystemRoleUsecase(scenario.access_control, scenario.role_repo))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "role_id": TECNICO_ROLE_ID,
            "name": "Técnico", "actions": ["tracking.start"], "is_default": True,
        }))

        assert response.status_code == 200
        assert response.body["is_default"] is True

    def test_unknown_role_returns_404(self):
        scenario = AccessScenario()
        controller = UpdateSystemRoleController(UpdateSystemRoleUsecase(scenario.access_control, scenario.role_repo))

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "role_id": "r-x", "name": "X", "actions": [],
        }))

        assert response.status_code == 404
