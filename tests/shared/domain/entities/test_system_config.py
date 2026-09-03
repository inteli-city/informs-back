import pytest

from src.shared.domain.entities.system_config import SystemConfig
from src.shared.helpers.errors.domain_errors import EntityError


def _config(**overrides) -> SystemConfig:
    base = {"system": "UBERLANDIA", "created_at": 1, "updated_at": 1}
    base.update(overrides)
    return SystemConfig(**base)


class TestSystemConfig:
    def test_creates_with_all_fields(self):
        config = _config(
            scope_keys=["bairro"],
            scope_partition_key="bairro",
            geofence_radius_m=200,
            allow_unassigned_forms=True,
        )
        assert config.scope_keys == ["bairro"]
        assert config.scope_partition_key == "bairro"
        assert config.geofence_radius_m == 200.0
        assert config.allow_unassigned_forms is True

    def test_creates_with_defaults(self):
        config = _config()
        assert config.scope_keys == []
        assert config.scope_partition_key is None
        assert config.geofence_radius_m is None
        assert config.allow_unassigned_forms is False

    def test_rejects_blank_system(self):
        with pytest.raises(EntityError):
            _config(system="")

    def test_rejects_non_string_scope_keys(self):
        with pytest.raises(EntityError):
            _config(scope_keys=["bairro", 1])

    def test_rejects_non_bool_allow_unassigned_forms(self):
        with pytest.raises(EntityError):
            _config(allow_unassigned_forms="true")

    def test_rejects_non_numeric_geofence_radius(self):
        with pytest.raises(EntityError):
            _config(geofence_radius_m="200")
