"""Grupos na criação do formulário (ADR-0022)."""

from copy import deepcopy

import pytest

from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock
from src.shared.infra.repositories.system_group_repository_mock import (
    MOCK_GROUP_A_ID,
    MOCK_GROUP_B_ID,
    SystemGroupRepositoryMock,
)
from tests.modules.create_form.app.test_create_form_usecase import _make_usecase_and_payload


def _pool_usecase() -> CreateFormUsecase:
    system_config_repo = SystemConfigRepositoryMock()
    system_config_repo.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, allow_unassigned_forms=True))
    return CreateFormUsecase(
        FormRepositoryMock(), FileRepositoryMock(), system_config_repo=system_config_repo,
        group_repo=SystemGroupRepositoryMock(),
    )


def _pool_payload(**overrides) -> dict:
    _, payload, _ = _make_usecase_and_payload()
    payload = deepcopy(payload)
    payload["user_id"] = None
    payload.update(overrides)
    return payload


class TestCreateFormGroupsUsecase:
    def test_open_form_keeps_its_groups(self):
        form, _ = _pool_usecase()(**_pool_payload(groups=[MOCK_GROUP_A_ID, MOCK_GROUP_B_ID]))

        assert form.user_id is None
        assert form.groups == [MOCK_GROUP_A_ID, MOCK_GROUP_B_ID]

    def test_unknown_group_is_rejected(self):
        with pytest.raises(EntityError):
            _pool_usecase()(**_pool_payload(groups=[MOCK_GROUP_A_ID, "equipe-z"]))

    def test_directed_form_may_carry_groups_for_a_later_release(self):
        _, payload, _ = _make_usecase_and_payload()
        form, _ = _pool_usecase()(**{**payload, "groups": [MOCK_GROUP_A_ID]})

        assert form.user_id is not None
        assert form.groups == [MOCK_GROUP_A_ID]

    def test_without_groups_nothing_changes(self):
        form, _ = _pool_usecase()(**_pool_payload())
        assert form.groups == []

    def test_groups_without_repository_fail_loudly(self):
        usecase, payload, _ = _make_usecase_and_payload()
        with pytest.raises(EntityError):
            usecase(**{**payload, "groups": [MOCK_GROUP_A_ID]})


class TestCreateFormGroupsController:
    def _body(self, groups):
        return {
            "requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001", "name": "Apex", "email": "apex@example.com",
                "cognito:groups": "FORMULARIOS,GAIA",
            },
            "form_title": "Tapa-buraco", "system": "GAIA", "city": "Uberlândia", "street": "Rua 1",
            "latitude": -18.9, "longitude": -48.2, "priority": 1,
            "justifications": [{"option": "o", "required_image": False, "required_text": False}],
            "sections": [{"section_id": 1, "fields": [{"field_type": "TEXT_FIELD", "key": "k", "label": "Comentário", "order": 1, "required": False}]}],
            "groups": groups,
        }

    def test_returns_groups_in_the_response(self):
        response = CreateFormController(_pool_usecase())(HttpRequest(body=self._body([MOCK_GROUP_A_ID])))

        assert response.status_code == 201, response.body
        assert response.body["groups"] == [MOCK_GROUP_A_ID]

    def test_unknown_group_returns_400(self):
        response = CreateFormController(_pool_usecase())(HttpRequest(body=self._body(["equipe-z"])))
        assert response.status_code == 400

    def test_malformed_group_id_returns_400(self):
        response = CreateFormController(_pool_usecase())(HttpRequest(body=self._body(["Equipe A"])))
        assert response.status_code == 400
