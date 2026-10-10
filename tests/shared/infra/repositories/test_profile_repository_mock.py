import pytest

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.repositories.profile_repository_mock import (
    MOCK_INSPECTOR_ID,
    MOCK_SUPER_ADMIN_ID,
    ProfileRepositoryMock,
)
from src.shared.infra.repositories.system_role_repository_mock import MOCK_TECNICO_ROLE_ID


class TestProfileRepositoryMock:
    def test_seeded_with_super_admin_and_field_person(self):
        repo = ProfileRepositoryMock()
        assert repo.get_by_user_id(MOCK_SUPER_ADMIN_ID).super_admin is True
        assert repo.get_by_user_id(MOCK_INSPECTOR_ID).super_admin is False
        assert repo.get_membership(MOCK_INSPECTOR_ID, "GAIA").role_id == MOCK_TECNICO_ROLE_ID

    def test_get_by_user_id_returns_deepcopy(self):
        repo = ProfileRepositoryMock()
        profile = repo.get_by_user_id(repo.profiles[0].user_id)
        assert profile is not None
        assert profile.user_id == repo.profiles[0].user_id
        # mutar o retornado não deve afetar o storage interno
        profile.deactivate(updated_at=1)
        assert repo.profiles[0].active is True

    def test_get_by_user_id_returns_none_when_missing(self):
        repo = ProfileRepositoryMock()
        assert repo.get_by_user_id("00000000-0000-0000-0000-000000000000") is None

    def test_create_new_profile(self):
        repo = ProfileRepositoryMock()
        new_profile = Profile(
            user_id="d61dbf66-a10f-11ed-a8fc-0242ac120099",
            name="New Inspector",
            email="new@example.com",
            active=True,
            created_at=1000,
            updated_at=1000,
        )
        created = repo.create(new_profile)
        assert created.user_id == new_profile.user_id
        assert repo.get_by_user_id(new_profile.user_id) is not None

    def test_create_duplicate_raises(self):
        repo = ProfileRepositoryMock()
        existing = repo.profiles[0]
        with pytest.raises(DuplicatedItem):
            repo.create(existing)

    def test_soft_delete_marks_inactive(self):
        repo = ProfileRepositoryMock()
        target = repo.profiles[1]
        result = repo.soft_delete(user_id=target.user_id, updated_at=2000)
        assert result.active is False
        assert result.updated_at == 2000
        assert repo.profiles[1].active is False

    def test_soft_delete_missing_raises(self):
        repo = ProfileRepositoryMock()
        with pytest.raises(NoItemsFound):
            repo.soft_delete(user_id="00000000-0000-0000-0000-000000000000", updated_at=1)

    def test_count_active_super_admins(self):
        repo = ProfileRepositoryMock()
        assert repo.count_active_super_admins() == 1

        repo.soft_delete(user_id=MOCK_SUPER_ADMIN_ID, updated_at=1)
        assert repo.count_active_super_admins() == 0

    def test_put_membership_replaces_the_role_in_the_system(self):
        repo = ProfileRepositoryMock()
        repo.put_membership(SystemMembership(
            user_id=MOCK_INSPECTOR_ID, system="GAIA", role_id="r-outro", created_at=1, updated_at=2,
        ))

        assert [m.role_id for m in repo.get_memberships(MOCK_INSPECTOR_ID)] == ["r-outro"]
        assert repo.count_memberships_by_role("GAIA", "r-outro") == 1
        assert repo.count_memberships_by_role("GAIA", MOCK_TECNICO_ROLE_ID) == 0

    def test_list_and_delete_memberships_by_system(self):
        repo = ProfileRepositoryMock()
        assert [m.user_id for m in repo.list_memberships_by_system("GAIA")] == [MOCK_INSPECTOR_ID]

        repo.delete_membership(MOCK_INSPECTOR_ID, "GAIA")

        assert repo.get_membership(MOCK_INSPECTOR_ID, "GAIA") is None
        assert repo.list_memberships_by_system("GAIA") == []
