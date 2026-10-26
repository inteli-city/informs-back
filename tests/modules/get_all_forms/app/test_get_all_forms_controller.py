import os
import sys

sys.path.append(os.getcwd())
from src.modules.get_all_forms.app.get_all_forms_controller import GetAllFormsController
from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


class _SpyPoolUsecase(GetAllFormsUsecase):
    """Usecase de escuta: registra o `limit` recebido sem mudar comportamento."""

    def __init__(self, repo):
        super().__init__(repo)
        self.received_limit = None

    def __call__(self, **kwargs):
        self.received_limit = kwargs.get("limit")
        return super().__call__(**kwargs)


def _pool_form(**overrides) -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    section = Section(section_id=1, fields=[text_field])
    base = dict(
        id='d61dbf66-a10f-11ed-a8fc-0242ac120040', form_title='FORM TITLE', created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
        user_id=None, system='GAIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )
    base.update(overrides)
    return Form(**base)


def _pool_request_body(repo, **extra) -> dict:
    body = {
        "requester_user": {
            "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120002", "name": "User", "email": "user@test.com",
            "cognito:groups": "FORMULARIOS,GAIA",
        },
        "scope": "pool",
        "system": "GAIA",
    }
    body.update(extra)
    return body


class TestGetAllFormsController:
    def test_get_all_forms_controller_success(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id,
                "name": "User",
                "email": "user@test.com",
                "cognito:groups": "FORMULARIOS,GAIA"
            },
            "limit": 20,
            "status": "PENDING",
            "system": repo.forms[0].system
        })

        response = controller(request)

        assert response.status_code == 200
        assert len(response.body["forms"]) == 1
        assert response.body["forms"][0]["status"] == "PENDING"
        assert response.body["last_evaluated_key"] is None

    def test_get_all_forms_controller_invalid_limit(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id,
                "name": "User",
                "email": "user@test.com",
                "cognito:groups": "FORMULARIOS,GAIA"
            },
            "limit": 0
        })

        response = controller(request)

        assert response.status_code == 400
        assert "limit" in response.body

    def test_get_all_forms_controller_status_list(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(
            body={
                "requester_user": {
                    "sub": repo.forms[0].user_id,
                    "name": "User",
                    "email": "user@test.com",
                    "cognito:groups": "FORMULARIOS,GAIA"
                },
                "limit": 20,
            },
            query_params={
                "status": ["PENDING", "IN_PROGRESS"]
            }
        )

        response = controller(request)

        assert response.status_code == 200
        assert len(response.body["forms"]) == 2
        statuses = {item["status"] for item in response.body["forms"]}
        assert statuses == {"PENDING", "IN_PROGRESS"}


class TestGetAllFormsControllerScope:
    def test_invalid_scope_returns_400(self):
        repo = FormRepositoryMock()
        controller = GetAllFormsController(GetAllFormsUsecase(repo))

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id, "name": "User", "email": "user@test.com",
                "cognito:groups": "FORMULARIOS,GAIA",
            },
            "scope": "not-a-valid-scope",
        })

        response = controller(request)
        assert response.status_code == 400


class TestGetAllFormsControllerPoolLimit:
    """A resposta do pool deve informar o limite que de fato valeu (IGZ-02)."""

    def _repo_with_pool(self, quantidade: int) -> FormRepositoryMock:
        repo = FormRepositoryMock()
        for i in range(quantidade):
            repo.forms.append(_pool_form(
                id=f'd61dbf66-a10f-11ed-a8fc-0242ac1{i:05d}', created_at=i,
            ))
        return repo

    def test_pool_without_limit_responds_effective_limit_200(self):
        repo = self._repo_with_pool(205)
        usecase = _SpyPoolUsecase(repo)
        controller = GetAllFormsController(usecase)

        response = controller(HttpRequest(body=_pool_request_body(repo)))

        assert response.status_code == 200
        assert usecase.received_limit == 200
        assert response.body["limit"] == 200
        assert response.body["last_evaluated_key"] is not None

    def test_pool_with_informed_limit_repeats_it(self):
        repo = self._repo_with_pool(60)
        usecase = _SpyPoolUsecase(repo)
        controller = GetAllFormsController(usecase)

        response = controller(HttpRequest(body=_pool_request_body(repo, limit=50)))

        assert response.status_code == 200
        assert usecase.received_limit == 50
        assert response.body["limit"] == 50

    def test_mine_without_limit_keeps_limit_null(self):
        repo = FormRepositoryMock()
        usecase = _SpyPoolUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id, "name": "User", "email": "user@test.com",
                "cognito:groups": "FORMULARIOS,GAIA",
            },
        })
        response = controller(request)

        assert response.status_code == 200
        assert usecase.received_limit is None
        assert response.body["limit"] is None
