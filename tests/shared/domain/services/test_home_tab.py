"""Aba inicial por role (`home_tab`): gravada no role, devolvida no login."""

import pytest

from src.modules.create_system_role.app.create_system_role_controller import CreateSystemRoleController
from src.modules.create_system_role.app.create_system_role_usecase import CreateSystemRoleUsecase
from src.modules.update_system_role.app.update_system_role_usecase import UpdateSystemRoleUsecase
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.home_tab_enum import HomeTab
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.dtos.system_role_dynamo_dto import SystemRoleDynamoDTO
from tests.modules.access_fixtures import (
    ADMIN_ID,
    GESTOR_ROLE_ID,
    MANAGER_ID,
    TECNICO_ROLE_ID,
    AccessScenario,
    requester_user,
)


FIELD_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120077"


def test_role_opens_on_the_list_by_default():
    role = SystemRole(system="GAIA", name="X", actions=[], created_at=1, updated_at=1)
    assert role.home_tab is HomeTab.LIST


def test_role_rejects_unknown_home_tab():
    with pytest.raises(EntityError):
        SystemRole(system="GAIA", name="X", actions=[], created_at=1, updated_at=1, home_tab="map")


def test_dto_round_trip_and_legacy_items():
    role = SystemRole(system="GAIA", name="X", actions=[], created_at=1, updated_at=1, home_tab=HomeTab.MAP)
    item = SystemRoleDynamoDTO.from_entity(role).to_dynamo()
    assert item["home_tab"] == "map"
    assert SystemRoleDynamoDTO.from_dynamo(item).to_entity().home_tab is HomeTab.MAP

    # Gravado antes do campo existir, ou com valor desconhecido: lista.
    del item["home_tab"]
    assert SystemRoleDynamoDTO.from_dynamo(item).to_entity().home_tab is HomeTab.LIST
    item["home_tab"] = "agenda"
    assert SystemRoleDynamoDTO.from_dynamo(item).to_entity().home_tab is HomeTab.LIST


def test_access_carries_the_home_tab_of_the_role():
    scenario = AccessScenario()
    UpdateSystemRoleUsecase(scenario.access_control, scenario.role_repo)(
        ADMIN_ID, "GAIA", TECNICO_ROLE_ID, "Técnico", [Action.TRACKING_START], True, HomeTab.MAP,
    )
    scenario.add_person(FIELD_ID, "Campo", "GAIA", TECNICO_ROLE_ID)

    assert scenario.access_control.access_in(FIELD_ID, "GAIA").home_tab is HomeTab.MAP
    # ADMIN é fixo: abre na lista.
    assert scenario.access_control.access_in(ADMIN_ID, "GAIA").home_tab is HomeTab.LIST


def test_marking_another_default_keeps_the_home_tab():
    scenario = AccessScenario()
    usecase = UpdateSystemRoleUsecase(scenario.access_control, scenario.role_repo)
    usecase(ADMIN_ID, "GAIA", TECNICO_ROLE_ID, "Técnico", [Action.TRACKING_START], True, HomeTab.CREATE)
    usecase(ADMIN_ID, "GAIA", GESTOR_ROLE_ID, "Gestor", [Action.FORMS_ASSIGN], True)

    tecnico = scenario.role_repo.get_role("GAIA", TECNICO_ROLE_ID)
    assert tecnico.is_default is False
    assert tecnico.home_tab is HomeTab.CREATE


def test_create_controller_accepts_and_validates_home_tab():
    scenario = AccessScenario()
    controller = CreateSystemRoleController(CreateSystemRoleUsecase(scenario.access_control, scenario.role_repo))
    body = {"requester_user": requester_user(MANAGER_ID), "system": "GAIA", "name": "Mapa", "actions": []}

    created = controller(HttpRequest(body={**body, "home_tab": "map"}))
    assert created.status_code == 201
    assert created.body["home_tab"] == "map"

    invalid = controller(HttpRequest(body={**body, "name": "Outro", "home_tab": "agenda"}))
    assert invalid.status_code == 400
