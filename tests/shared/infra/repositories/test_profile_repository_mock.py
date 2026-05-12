import pytest

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


class TestProfileRepositoryMock:
    def test_seeded_with_admin_and_inspector(self):
        repo = ProfileRepositoryMock()
        roles = {p.role for p in repo.profiles}
        assert PROFILE_ROLE.ADMIN in roles
        assert PROFILE_ROLE.INSPECTOR in roles

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
            role=PROFILE_ROLE.INSPECTOR,
            name="New Inspector",
            email="new@example.com",
            system="SGC",
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

    def test_count_active_by_role(self):
        repo = ProfileRepositoryMock()
        assert repo.count_active_by_role(PROFILE_ROLE.ADMIN) == 1
        assert repo.count_active_by_role(PROFILE_ROLE.INSPECTOR) == 1

        repo.soft_delete(user_id=repo.profiles[1].user_id, updated_at=1)
        assert repo.count_active_by_role(PROFILE_ROLE.INSPECTOR) == 0
