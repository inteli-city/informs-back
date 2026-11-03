import os
import sys
import time
import uuid

sys.path.append(os.getcwd())
from src.modules.get_all_forms.app.get_all_forms_controller import GetAllFormsController
from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.contracts.endpoints.get_all_forms_contract import GetAllFormsResponseSchema
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from tests.modules.access_fixtures import AccessScenario, give_role

REQUESTER_SUB = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
CREATED_BY = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
ANTIGO = 1_000_000  # bem antes de qualquer `server_time` do teste

justification = Justification(
    options=[JustificationOption(option='option', required_image=True, required_text=True)],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _form(updated_at: int) -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    return Form(
        id=str(uuid.uuid4()), form_title='FORM TITLE', created_by=CREATED_BY,
        user_id=None, system='GAIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=updated_at,
        justification=justification, sections=[Section(section_id=1, fields=[text_field])],
    )


def _repo(*forms: Form) -> FormRepositoryMock:
    repo = FormRepositoryMock()
    repo.forms = list(forms)
    return repo


def _controller(repo: FormRepositoryMock) -> GetAllFormsController:
    return GetAllFormsController(GetAllFormsUsecase(repo))


def _call(controller: GetAllFormsController, scope: str = "pool", **extra):
    body = {
        "requester_user": {"sub": REQUESTER_SUB, "name": "User", "email": "u@example.com",
                           "cognito:groups": "FORMULARIOS,GAIA"},
        "scope": scope,
        "system": "GAIA",
    }
    body.update(extra)
    return controller(HttpRequest(body=body))


class TestServerTimeEmTodaCarga:
    def test_carga_completa_pool_traz_server_time_inteiro_e_nao_futuro(self):
        controller = _controller(_repo(_form(updated_at=ANTIGO)))
        antes = int(time.time() * 1000)

        response = _call(controller, scope="pool")

        depois = int(time.time() * 1000)
        assert response.status_code == 200
        assert isinstance(response.body["server_time"], int)
        assert antes <= response.body["server_time"] <= depois

    def test_carga_completa_mine_traz_server_time(self):
        response = _call(_controller(_repo(_form(updated_at=ANTIGO))), scope="mine")

        assert response.status_code == 200
        assert response.body["server_time"] > 0

    def test_carga_completa_all_traz_server_time(self):
        # `scope=all` exige `forms.view_all` no sistema: a pessoa de teste recebe esse papel.
        scenario = AccessScenario()
        give_role(scenario.profile_repo, scenario.role_repo, REQUESTER_SUB, "GAIA", [Action.FORMS_VIEW_ALL])
        repo = _repo(_form(updated_at=ANTIGO))
        controller = GetAllFormsController(GetAllFormsUsecase(repo, scenario.access_control))

        response = _call(controller, scope="all")

        assert response.status_code == 200
        assert response.body["server_time"] > 0

    def test_busca_com_search_tambem_traz_server_time(self):
        response = _call(_controller(_repo(_form(updated_at=ANTIGO))), scope="mine", search="FORM")

        assert response.status_code == 200
        assert response.body["server_time"] > 0

    def test_segunda_pagina_traz_server_time_maior_ou_igual_ao_da_primeira(self):
        controller = _controller(_repo(*[_form(updated_at=ANTIGO) for _ in range(3)]))

        primeira = _call(controller, scope="pool", limit=2)
        segunda = _call(controller, scope="pool", limit=2,
                        exclusive_start_key=primeira.body["last_evaluated_key"])

        assert primeira.body["last_evaluated_key"] is not None
        assert segunda.body["server_time"] is not None
        assert segunda.body["server_time"] >= primeira.body["server_time"]


class TestCargaSeguidaDeDelta:
    def test_delta_com_o_server_time_da_primeira_pagina_pega_so_o_que_mudou(self):
        # Caso que o #103 não cobria sozinho: a carga completa entrega o `server_time`; uma alteração entre os
        # dois passos tem de voltar no delta, e nada mais.
        forms = [_form(updated_at=ANTIGO) for _ in range(4)]
        repo = _repo(*forms)
        controller = _controller(repo)

        primeira = _call(controller, scope="pool", limit=2)
        t1 = primeira.body["server_time"]

        alterado = forms[2]
        alterado.updated_at = int(time.time() * 1000)
        repo.forms[2].updated_at = alterado.updated_at

        delta = _call(controller, scope="pool", updated_after=t1 - 5000)

        ids = [item["id"] for item in delta.body["forms"]]
        assert ids == [alterado.id]

    def test_delta_multipagina_nao_repete_nem_perde_quem_mudou(self):
        forms = [_form(updated_at=ANTIGO) for _ in range(4)]
        repo = _repo(*forms)
        controller = _controller(repo)

        t1 = _call(controller, scope="pool", limit=2).body["server_time"]
        mudaram = [forms[0], forms[3]]
        for form in mudaram:
            repo.forms[repo.forms.index(form)].updated_at = int(time.time() * 1000)

        visto = []
        cursor = None
        while True:
            extra = {"updated_after": t1 - 5000, "limit": 1}
            if cursor is not None:
                extra["exclusive_start_key"] = cursor
            response = _call(controller, scope="pool", **extra)
            visto.extend(item["id"] for item in response.body["forms"])
            cursor = response.body["last_evaluated_key"]
            if cursor is None:
                break

        assert sorted(visto) == sorted(f.id for f in mudaram)


class TestCorpoComDeltaESemDelta:
    def test_com_updated_after_o_corpo_tem_as_chaves_do_delta_e_server_time(self):
        response = _call(_controller(_repo(_form(updated_at=ANTIGO))), scope="pool", updated_after=0)

        assert set(response.body.keys()) == {"forms", "limit", "last_evaluated_key", "server_time"}

    def test_clientes_antigos_validam_o_corpo_sem_server_time(self):
        # O esquema é retrocompatível: uma resposta sem o campo (formato de antes) ainda valida.
        validado = GetAllFormsResponseSchema.model_validate({"forms": [], "limit": 10, "last_evaluated_key": None})

        assert validado.server_time is None
