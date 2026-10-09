from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import ALL_ACTIONS, AccessControl
from src.shared.infra.repositories.profile_repository_mock import (
    MOCK_INSPECTOR_ID,
    MOCK_SUPER_ADMIN_ID,
    ProfileRepositoryMock,
)
from src.shared.infra.repositories.system_role_repository_mock import (
    MOCK_GESTOR_ROLE_ID,
    MOCK_TECNICO_ROLE_ID,
    SystemRoleRepositoryMock,
)


def _access_control():
    profile_repo = ProfileRepositoryMock()
    return AccessControl(profile_repo, SystemRoleRepositoryMock()), profile_repo


def _join(profile_repo, user_id, system, role_id):
    profile_repo.put_membership(SystemMembership(
        user_id=user_id, system=system, role_id=role_id, created_at=1, updated_at=1,
    ))


class TestAccessControl:
    def test_super_admin_can_everything_in_any_system(self):
        access_control, _ = _access_control()

        assert access_control.is_super_admin(MOCK_SUPER_ADMIN_ID) is True
        assert access_control.access_in(MOCK_SUPER_ADMIN_ID, "QUALQUER").actions == ALL_ACTIONS
        assert access_control.is_system_admin(MOCK_SUPER_ADMIN_ID, "QUALQUER") is True

    def test_role_gives_only_its_actions_in_its_system(self):
        access_control, _ = _access_control()

        assert access_control.can(MOCK_INSPECTOR_ID, "GAIA", Action.TRACKING_START) is True
        assert access_control.can(MOCK_INSPECTOR_ID, "GAIA", Action.FORMS_ASSIGN) is False
        assert access_control.can(MOCK_INSPECTOR_ID, "UBERLANDIA", Action.TRACKING_START) is False

    def test_admin_role_gives_every_action_only_in_that_system(self):
        access_control, profile_repo = _access_control()
        _join(profile_repo, MOCK_INSPECTOR_ID, "UBERLANDIA", ADMIN_ROLE_ID)

        assert access_control.is_system_admin(MOCK_INSPECTOR_ID, "UBERLANDIA") is True
        assert access_control.is_system_admin(MOCK_INSPECTOR_ID, "GAIA") is False
        assert access_control.is_super_admin(MOCK_INSPECTOR_ID) is False

    def test_inactive_profile_can_nothing(self):
        access_control, profile_repo = _access_control()
        profile_repo.soft_delete(MOCK_SUPER_ADMIN_ID, updated_at=1)

        assert access_control.access_in(MOCK_SUPER_ADMIN_ID, "GAIA").actions == frozenset()

    def test_unknown_profile_can_nothing(self):
        access_control, _ = _access_control()
        assert access_control.access_in("ghost", "GAIA").actions == frozenset()

    def test_membership_to_a_deleted_role_gives_nothing(self):
        access_control, profile_repo = _access_control()
        _join(profile_repo, MOCK_INSPECTOR_ID, "GAIA", "r-apagado")

        access = access_control.access_in(MOCK_INSPECTOR_ID, "GAIA")

        assert access.role_id == "r-apagado"
        assert access.actions == frozenset()

    def test_systems_where_lists_the_systems_with_the_action(self):
        access_control, profile_repo = _access_control()
        _join(profile_repo, MOCK_INSPECTOR_ID, "UBERLANDIA", ADMIN_ROLE_ID)

        assert access_control.systems_where(MOCK_INSPECTOR_ID, Action.TRACKING_START) == ["GAIA", "UBERLANDIA"]
        assert access_control.systems_where(MOCK_INSPECTOR_ID, Action.USERS_MANAGE) == ["UBERLANDIA"]

    def test_role_name_comes_with_the_access(self):
        access_control, profile_repo = _access_control()
        _join(profile_repo, MOCK_INSPECTOR_ID, "GAIA", MOCK_GESTOR_ROLE_ID)

        access = access_control.access_in(MOCK_INSPECTOR_ID, "GAIA")

        assert (access.role_id, access.role_name) == (MOCK_GESTOR_ROLE_ID, "Gestor")
        assert MOCK_TECNICO_ROLE_ID != access.role_id
