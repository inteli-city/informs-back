from src.shared.domain.entities.system_config import SystemConfig
from src.shared.infra.dtos.system_config_dynamo_dto import SystemConfigDynamoDTO
from src.shared.infra.repositories.system_config_repository_dynamo import SystemConfigRepositoryDynamo


class FakeSystemConfigDynamo:
    def __init__(self):
        self.get_item_response = {}
        self.put_calls = []

    def get_item(self, partition_key, sort_key=None):
        return self.get_item_response

    def put_item(self, item, partition_key, sort_key=None, **kwargs):
        self.put_calls.append((item, partition_key, sort_key, kwargs))
        return {}


def _repo() -> SystemConfigRepositoryDynamo:
    repo = SystemConfigRepositoryDynamo.__new__(SystemConfigRepositoryDynamo)
    repo.dynamo = FakeSystemConfigDynamo()
    return repo


def _config(**overrides) -> SystemConfig:
    base = {"system": "UBERLANDIA", "created_at": 1, "updated_at": 1, "allow_unassigned_forms": True}
    base.update(overrides)
    return SystemConfig(**base)


class TestSystemConfigRepositoryDynamo:
    def test_get_by_system_not_found(self):
        repo = _repo()
        repo.dynamo.get_item_response = {}
        assert repo.get_by_system("UBERLANDIA") is None

    def test_get_by_system_found(self):
        repo = _repo()
        item = SystemConfigDynamoDTO.from_entity(_config()).to_dynamo()
        repo.dynamo.get_item_response = {"Item": item}

        config = repo.get_by_system("UBERLANDIA")
        assert config is not None
        assert config.allow_unassigned_forms is True

    def test_put_writes_with_correct_keys(self):
        repo = _repo()
        repo.put(_config())

        _, pk, sk, _ = repo.dynamo.put_calls[0]
        assert pk == "system#UBERLANDIA"
        assert sk == "CONFIG"
