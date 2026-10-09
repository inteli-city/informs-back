import pytest

from src.shared.domain.entities.app_config import AppConfig
from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.helpers.errors.domain_errors import EntityError


class TestAppConfig:
    def test_defaults_match_current_app(self):
        config = AppConfig.resolve()

        assert config.menus.create_form is True
        assert config.menus.start_tracking is True
        assert config.menus.route_plan is True
        assert config.map.cluster_max_zoom == 16
        assert config.texts.claim_action_label == "Assumir formulário"
        assert config.flows.open_form_after_claim is False
        assert config.flows.return_to_map_after_submit is False
        assert config.flows.cancel_form is False
        assert config.preview.information_images is False

    def test_system_layer_overrides_default_layer_key_by_key(self):
        default_layer = {"menus": {"route_plan": False}, "texts": {"claim_action_label": "Atender"}}
        system_layer = {"texts": {"claim_action_label": "Executar serviço"}}

        config = AppConfig.resolve(default_layer, system_layer)

        assert config.menus.route_plan is False
        assert config.menus.create_form is True
        assert config.texts.claim_action_label == "Executar serviço"

    def test_resolve_does_not_mutate_layers(self):
        default_layer = {"menus": {"route_plan": False}}
        AppConfig.resolve(default_layer, {"menus": {"create_form": False}})
        assert default_layer == {"menus": {"route_plan": False}}

    def test_validate_layer_keeps_only_given_keys(self):
        layer = {"flows": {"cancel_form": True}}
        assert AppConfig.validate_layer(layer) == layer

    def test_validate_layer_rejects_unknown_key(self):
        with pytest.raises(EntityError) as err:
            AppConfig.validate_layer({"flows": {"cancel_from": True}})
        assert "flows.cancel_from" in err.value.message

    def test_validate_layer_rejects_out_of_range_value(self):
        with pytest.raises(EntityError):
            AppConfig.validate_layer({"map": {"cluster_max_zoom": 40}})

    def test_validate_layer_rejects_non_dict(self):
        with pytest.raises(EntityError):
            AppConfig.validate_layer(["menus"])


class TestDefaultAppConfig:
    def test_creates_with_valid_layer(self):
        config = DefaultAppConfig(values={"menus": {"route_plan": False}}, version=2, updated_at=10, updated_by="admin")
        assert config.values == {"menus": {"route_plan": False}}
        assert config.version == 2

    def test_rejects_invalid_layer(self):
        with pytest.raises(EntityError):
            DefaultAppConfig(values={"menus": {"nope": True}}, version=1, updated_at=1)

    def test_rejects_negative_version(self):
        with pytest.raises(EntityError):
            DefaultAppConfig(values={}, version=-1, updated_at=1)
