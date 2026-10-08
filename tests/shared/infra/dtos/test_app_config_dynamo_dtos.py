from decimal import Decimal

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.infra.dtos.default_app_config_dynamo_dto import DefaultAppConfigDynamoDTO
from src.shared.infra.dtos.system_config_dynamo_dto import SystemConfigDynamoDTO


class TestSystemConfigAppConfigDTO:
    def test_round_trip_with_decimal_from_dynamo(self):
        item = {
            "system": "UBERLANDIA",
            "created_at": Decimal("1"),
            "updated_at": Decimal("2"),
            "app_config": {"map": {"cluster_max_zoom": Decimal("14")}, "menus": {"route_plan": False}},
            "app_config_version": Decimal("4"),
        }

        config = SystemConfigDynamoDTO.from_dynamo(item).to_entity()

        assert config.app_config == {"map": {"cluster_max_zoom": 14}, "menus": {"route_plan": False}}
        assert isinstance(config.app_config["map"]["cluster_max_zoom"], int)
        assert config.app_config_version == 4

    def test_item_without_app_config_reads_as_empty_layer(self):
        item = {"system": "GAIA", "created_at": 1, "updated_at": 1}
        config = SystemConfigDynamoDTO.from_dynamo(item).to_entity()
        assert config.app_config == {}
        assert config.app_config_version == 0

    def test_to_dynamo_includes_app_config(self):
        config = SystemConfig(
            system="UBERLANDIA", created_at=1, updated_at=1,
            app_config={"flows": {"cancel_form": True}}, app_config_version=1,
        )
        item = SystemConfigDynamoDTO.from_entity(config).to_dynamo()
        assert item["app_config"] == {"flows": {"cancel_form": True}}
        assert item["app_config_version"] == 1


class TestDefaultAppConfigDTO:
    def test_round_trip(self):
        config = DefaultAppConfig(values={"texts": {"claim_action_label": "Atender"}}, version=2, updated_at=5, updated_by="admin")
        item = DefaultAppConfigDynamoDTO.from_entity(config).to_dynamo()
        back = DefaultAppConfigDynamoDTO.from_dynamo({**item, "version": Decimal("2"), "updated_at": Decimal("5")}).to_entity()

        assert back.values == config.values
        assert back.version == 2
        assert back.updated_by == "admin"

    def test_keys(self):
        assert DefaultAppConfigDynamoDTO.build_pk() == "app_config#DEFAULT"
        assert DefaultAppConfigDynamoDTO.build_sk() == "CONFIG"
