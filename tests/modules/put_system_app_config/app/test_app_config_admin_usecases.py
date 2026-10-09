import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.get_app_config_admin.app.get_app_config_admin_usecase import GetAppConfigAdminUsecase
from src.modules.put_default_app_config.app.put_default_app_config_usecase import PutDefaultAppConfigUsecase
from src.modules.put_system_app_config.app.put_system_app_config_usecase import PutSystemAppConfigUsecase
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock

PLATFORM_ADMIN = "d61dbf66-a10f-11ed-a8fc-0242ac120001"  # role ADMIN no mock
INSPECTOR = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


def _requester(user_id, *systems):
    return UserGatewayDTO(user_id=user_id, name="User", email="user@test.com", systems=list(systems))


class _Base:
    def setup_method(self):
        self.profiles = ProfileRepositoryMock()
        self.configs = SystemConfigRepositoryMock()

    def make_system_admin(self, *systems):
        self.profiles.update_profile(user_id=INSPECTOR, admin_systems=list(systems))


class TestGetAppConfigAdmin(_Base):
    def test_inspector_without_admin_systems_is_forbidden(self):
        with pytest.raises(ForbiddenAction):
            GetAppConfigAdminUsecase(self.profiles, self.configs)(_requester(INSPECTOR, "GAIA"))

    def test_platform_admin_sees_every_known_system_and_can_edit_default(self):
        self.configs.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, app_config={"menus": {"create_form": False}}, app_config_version=2))

        result = GetAppConfigAdminUsecase(self.profiles, self.configs)(_requester(PLATFORM_ADMIN, "GAIA"))

        assert result.can_edit_default is True
        assert [item.system for item in result.systems] == ["GAIA", "UBERLANDIA"]
        uberlandia = result.systems[1]
        assert uberlandia.values == {"menus": {"create_form": False}}
        assert uberlandia.version == 2
        assert uberlandia.effective.menus.create_form is False

    def test_system_admin_sees_only_the_systems_they_administer(self):
        self.make_system_admin("UBERLANDIA")

        result = GetAppConfigAdminUsecase(self.profiles, self.configs)(_requester(INSPECTOR, "GAIA", "UBERLANDIA"))

        assert result.can_edit_default is False
        assert [item.system for item in result.systems] == ["UBERLANDIA"]

    def test_effective_matches_what_the_app_receives(self):
        # "Em aberto" ligado na camada, mas o sistema não aceita formulário sem
        # dono: o app recebe desligado, e o Admin tem que mostrar o mesmo.
        open_layer = {"creation": {"allow_open": True}}
        self.configs.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, app_config=open_layer, app_config_version=1))
        self.configs.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, allow_unassigned_forms=True, app_config=open_layer, app_config_version=1))

        result = GetAppConfigAdminUsecase(self.profiles, self.configs)(_requester(PLATFORM_ADMIN))
        effective = {item.system: item.effective.creation.allow_open for item in result.systems}

        assert effective == {"GAIA": False, "UBERLANDIA": True}


class TestPutDefaultAppConfig(_Base):
    def test_platform_admin_saves_and_bumps_version(self):
        usecase = PutDefaultAppConfigUsecase(self.profiles, self.configs)
        saved = usecase(_requester(PLATFORM_ADMIN), {"menus": {"route_plan": False}}, base_version=0)
        assert saved.version == 1
        assert self.configs.get_default_app_config().values == {"menus": {"route_plan": False}}

    def test_stale_base_version_is_rejected(self):
        usecase = PutDefaultAppConfigUsecase(self.profiles, self.configs)
        usecase(_requester(PLATFORM_ADMIN), {"menus": {"route_plan": False}}, base_version=0)
        with pytest.raises(DuplicatedItem):
            usecase(_requester(PLATFORM_ADMIN), {}, base_version=0)

    def test_system_admin_cannot_edit_default(self):
        self.make_system_admin("UBERLANDIA")
        with pytest.raises(ForbiddenAction):
            PutDefaultAppConfigUsecase(self.profiles, self.configs)(_requester(INSPECTOR), {}, base_version=0)

    def test_invalid_layer_is_rejected(self):
        with pytest.raises(EntityError):
            PutDefaultAppConfigUsecase(self.profiles, self.configs)(_requester(PLATFORM_ADMIN), {"menus": {"nope": True}}, base_version=0)


class TestPutSystemAppConfig(_Base):
    def test_system_admin_saves_own_system_preserving_other_fields(self):
        self.configs.put(SystemConfig(system="UBERLANDIA", created_at=1, updated_at=1, allow_unassigned_forms=True))
        self.make_system_admin("UBERLANDIA")

        saved = PutSystemAppConfigUsecase(self.profiles, self.configs)(
            _requester(INSPECTOR), "UBERLANDIA", {"texts": {"claim_action_label": "Executar serviço"}}, base_version=0
        )

        assert saved.version == 1
        assert saved.effective.texts.claim_action_label == "Executar serviço"
        stored = self.configs.get_by_system("UBERLANDIA")
        assert stored.allow_unassigned_forms is True
        assert stored.app_config_version == 1

    def test_saved_effective_respects_unassigned_forms(self):
        self.configs.put(SystemConfig(system="GAIA", created_at=1, updated_at=1))

        saved = PutSystemAppConfigUsecase(self.profiles, self.configs)(
            _requester(PLATFORM_ADMIN), "GAIA", {"creation": {"allow_open": True}}, base_version=0
        )

        assert saved.values == {"creation": {"allow_open": True}}
        assert saved.effective.creation.allow_open is False

    def test_system_admin_cannot_edit_another_system(self):
        self.make_system_admin("UBERLANDIA")
        with pytest.raises(ForbiddenAction):
            PutSystemAppConfigUsecase(self.profiles, self.configs)(_requester(INSPECTOR), "GAIA", {}, base_version=0)

    def test_platform_admin_can_edit_any_system(self):
        saved = PutSystemAppConfigUsecase(self.profiles, self.configs)(
            _requester(PLATFORM_ADMIN), "GAIA", {"flows": {"cancel_form": True}}, base_version=0
        )
        assert saved.effective.flows.cancel_form is True

    def test_stale_base_version_is_rejected(self):
        self.configs.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, app_config_version=3))
        with pytest.raises(DuplicatedItem):
            PutSystemAppConfigUsecase(self.profiles, self.configs)(_requester(PLATFORM_ADMIN), "GAIA", {}, base_version=2)
