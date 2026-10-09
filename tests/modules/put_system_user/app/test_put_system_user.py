import pytest

from src.modules.put_system_user.app.put_system_user_controller import PutSystemUserController
from src.modules.put_system_user.app.put_system_user_usecase import PutSystemUserUsecase
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    INSPECTOR_ID,
    MANAGER_ID,
    SUPER_ADMIN_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


NEW_PERSON_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120005"


class TestPutSystemUserUsecase:
    def setup_method(self):
        self.scenario = AccessScenario()
        self.scenario.add_person(NEW_PERSON_ID, "Nova Pessoa")
        self.usecase = PutSystemUserUsecase(
            self.scenario.access_control, self.scenario.profile_repo, self.scenario.role_repo,
        )

    def test_system_admin_gives_a_role(self):
        saved = self.usecase(ADMIN_ID, "GAIA", NEW_PERSON_ID, GESTOR_ROLE_ID)

        assert saved.role_name == "Gestor"
        assert self.scenario.profile_repo.get_membership(NEW_PERSON_ID, "GAIA").role_id == GESTOR_ROLE_ID

    def test_changing_the_role_keeps_created_at(self):
        saved = self.usecase(ADMIN_ID, "GAIA", INSPECTOR_ID, GESTOR_ROLE_ID)
        assert saved.membership.created_at == 946684800000

    def test_only_super_admin_gives_admin(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(ADMIN_ID, "GAIA", NEW_PERSON_ID, ADMIN_ROLE_ID)

        saved = self.usecase(SUPER_ADMIN_ID, "GAIA", NEW_PERSON_ID, ADMIN_ROLE_ID)
        assert saved.role_name == "Administrador"

    def test_only_super_admin_takes_admin_away(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", ADMIN_ID, TECNICO_ROLE_ID)

    def test_manager_cannot_give_a_role_with_actions_they_do_not_have(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(MANAGER_ID, "GAIA", NEW_PERSON_ID, GESTOR_ROLE_ID)

    def test_manager_gives_a_role_within_their_actions(self):
        saved = self.usecase(MANAGER_ID, "GAIA", NEW_PERSON_ID, TECNICO_ROLE_ID)
        assert saved.membership.role_id == TECNICO_ROLE_ID

    def test_without_users_manage_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(INSPECTOR_ID, "GAIA", NEW_PERSON_ID, TECNICO_ROLE_ID)

    def test_unknown_person_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(ADMIN_ID, "GAIA", "d61dbf66-a10f-11ed-a8fc-0242ac129999", TECNICO_ROLE_ID)

    def test_role_from_another_system_is_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(SUPER_ADMIN_ID, "UBERLANDIA", NEW_PERSON_ID, TECNICO_ROLE_ID)


class TestPutSystemUserController:
    def test_returns_200(self):
        scenario = AccessScenario()
        scenario.add_person(NEW_PERSON_ID, "Nova Pessoa")
        controller = PutSystemUserController(
            PutSystemUserUsecase(scenario.access_control, scenario.profile_repo, scenario.role_repo)
        )

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "user_id": NEW_PERSON_ID,
            "role_id": TECNICO_ROLE_ID,
        }))

        assert response.status_code == 200
        assert response.body == {
            "system": "GAIA", "user_id": NEW_PERSON_ID, "role_id": TECNICO_ROLE_ID, "role_name": "Técnico",
        }

    def test_admin_without_super_admin_returns_403(self):
        scenario = AccessScenario()
        controller = PutSystemUserController(
            PutSystemUserUsecase(scenario.access_control, scenario.profile_repo, scenario.role_repo)
        )

        response = controller(HttpRequest(body={
            "requester_user": requester_user(ADMIN_ID), "system": "GAIA", "user_id": INSPECTOR_ID, "role_id": "ADMIN",
        }))

        assert response.status_code == 403
