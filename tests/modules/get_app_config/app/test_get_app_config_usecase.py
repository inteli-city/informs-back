import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_app_config.app.get_app_config_usecase import GetAppConfigUsecase
from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock


def _requester(*systems):
    return UserGatewayDTO(user_id="user-123", name="User", email="user@test.com", systems=list(systems))


class TestGetAppConfigUsecase:
    def setup_method(self):
        self.repo = SystemConfigRepositoryMock()
        self.usecase = GetAppConfigUsecase(self.repo)

    def test_without_any_layer_returns_schema_defaults(self):
        result = self.usecase(requester=_requester("GAIA"))

        assert result.default.version == "0"
        assert result.default.config.menus.create_form is True
        assert len(result.systems) == 1
        assert result.systems[0].system == "GAIA"
        assert result.systems[0].version == "0.0"
        assert result.systems[0].config == result.default.config

    def test_system_inherits_default_and_applies_its_differences(self):
        self.repo.put_default_app_config(DefaultAppConfig(values={"menus": {"route_plan": False}}, version=2, updated_at=1))
        self.repo.put(SystemConfig(
            system="UBERLANDIA", created_at=1, updated_at=1,
            app_config={"menus": {"create_form": False}, "texts": {"claim_action_label": "Executar serviço"}},
            app_config_version=5,
        ))

        result = self.usecase(requester=_requester("UBERLANDIA", "GAIA"))
        by_system = {item.system: item for item in result.systems}

        uberlandia = by_system["UBERLANDIA"]
        assert uberlandia.version == "2.5"
        assert uberlandia.config.menus.route_plan is False
        assert uberlandia.config.menus.create_form is False
        assert uberlandia.config.texts.claim_action_label == "Executar serviço"

        gaia = by_system["GAIA"]
        assert gaia.version == "2.0"
        assert gaia.config.menus.route_plan is False
        assert gaia.config.menus.create_form is True
        assert gaia.config.texts.claim_action_label == "Assumir formulário"

    def test_user_without_systems_gets_only_default(self):
        result = self.usecase(requester=_requester())
        assert result.systems == []

    def test_allow_open_is_off_when_system_does_not_accept_unassigned_forms(self):
        self.repo.put_default_app_config(DefaultAppConfig(values={"creation": {"allow_open": True}}, version=1, updated_at=1))
        self.repo.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, allow_unassigned_forms=True))
        self.repo.put(SystemConfig(system="GEOVISTA", created_at=1, updated_at=1, allow_unassigned_forms=False))

        result = self.usecase(requester=_requester("UBERLANDIA", "GEOVISTA", "GAIA"))
        by_system = {item.system: item for item in result.systems}

        assert by_system["UBERLANDIA"].config.creation.allow_open is True
        assert by_system["GEOVISTA"].config.creation.allow_open is False
        assert by_system["GAIA"].config.creation.allow_open is False
        assert result.default.config.creation.allow_open is False
