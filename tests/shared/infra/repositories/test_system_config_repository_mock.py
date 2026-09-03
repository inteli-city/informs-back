from src.shared.domain.entities.system_config import SystemConfig
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock


class TestSystemConfigRepositoryMock:
    def test_get_by_system_none_when_empty(self):
        repo = SystemConfigRepositoryMock()
        assert repo.get_by_system("UBERLANDIA") is None

    def test_put_and_get_round_trip(self):
        repo = SystemConfigRepositoryMock()
        config = SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, allow_unassigned_forms=True)

        repo.put(config)
        fetched = repo.get_by_system("UBERLANDIA")

        assert fetched is not None
        assert fetched.allow_unassigned_forms is True
        assert repo.get_by_system("GAIA") is None

    def test_put_overwrites_existing_config_for_same_system(self):
        repo = SystemConfigRepositoryMock()
        repo.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, allow_unassigned_forms=False))
        repo.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=2, allow_unassigned_forms=True))

        fetched = repo.get_by_system("UBERLANDIA")
        assert fetched.allow_unassigned_forms is True
        assert fetched.updated_at == 2
        assert len(repo.configs) == 1
