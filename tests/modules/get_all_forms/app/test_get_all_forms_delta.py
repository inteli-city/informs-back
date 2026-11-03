import os
import sys
import time
import uuid

sys.path.append(os.getcwd())
from src.modules.get_all_forms.app.get_all_forms_controller import GetAllFormsController
from src.modules.get_all_forms.app.get_all_forms_usecase import POOL_DEFAULT_LIMIT, GetAllFormsUsecase
from src.modules.get_all_forms.app.get_all_forms_viewmodel import GetAllFormsViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

REQUESTER_SUB = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
OTHER_SUB = "d61dbf66-a10f-11ed-a8fc-0242ac120003"
CREATED_BY = "d61dbf66-a10f-11ed-a8fc-0242ac120001"

justification = Justification(
    options=[JustificationOption(option='option', required_image=True, required_text=True)],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _form(updated_at: int, owner: str | None = None, system: str = "GAIA", status=FormStatus.PENDING) -> Form:
    """Uma OS. Sem dono ela está no pool (`Possession.OPEN`); com dono, já foi reivindicada."""
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    return Form(
        id=str(uuid.uuid4()), form_title='FORM TITLE', created_by=CREATED_BY,
        user_id=owner, system=system, street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=status, created_at=1, updated_at=updated_at,
        justification=justification, sections=[Section(section_id=1, fields=[text_field])],
    )


def _repo(*forms: Form) -> FormRepositoryMock:
    repo = FormRepositoryMock()
    repo.forms = list(forms)
    return repo


def _body(**extra) -> dict:
    body = {
        "requester_user": {
            "sub": REQUESTER_SUB, "name": "User", "email": "user@test.com",
            "cognito:groups": "FORMULARIOS,GAIA",
        },
        "scope": "pool",
        "system": "GAIA",
    }
    body.update(extra)
    return body


def _call(repo, **extra):
    controller = GetAllFormsController(GetAllFormsUsecase(repo))
    return controller(HttpRequest(body=_body(**extra)))


class TestPoolDelta:
    def test_devolve_so_o_que_mudou_depois_do_instante_em_ordem_crescente(self):
        antigo = _form(updated_at=100)
        novo_b = _form(updated_at=300)
        novo_a = _form(updated_at=200)
        repo = _repo(novo_b, antigo, novo_a)

        response = _call(repo, updated_after=100)

        assert response.status_code == 200
        assert [f["id"] for f in response.body["forms"]] == [novo_a.id, novo_b.id]
        assert [f["updated_at"] for f in response.body["forms"]] == [200, 300]

    def test_o_instante_exato_nao_entra_de_novo(self):
        repo = _repo(_form(updated_at=500))

        response = _call(repo, updated_after=500)

        assert response.body["forms"] == []

    def test_os_que_estao_no_pool_voltam_completas(self):
        repo = _repo(_form(updated_at=200))

        form = _call(repo, updated_after=100).body["forms"][0]

        assert form["status"] == "PENDING"
        assert "form_title" in form
        assert "removed_from_pool" not in form

    def test_os_que_sairam_do_pool_voltam_so_como_marcador_minimo(self):
        saiu = _form(updated_at=200, owner=OTHER_SUB, status=FormStatus.COMPLETED)
        repo = _repo(saiu)

        marcador = _call(repo, updated_after=100).body["forms"][0]

        assert set(marcador.keys()) == {"id", "status", "possession", "updated_at", "removed_from_pool"}
        assert marcador == {
            "id": saiu.id,
            "status": "COMPLETED",
            "possession": "OWNED",
            "updated_at": 200,
            "removed_from_pool": True,
        }

    def test_paginacao_por_cursor_nao_repete_nem_perde(self):
        forms = [_form(updated_at=100 + i) for i in range(1, 6)]
        # Uma OS antiga no meio: o filtro do delta tem de deixá-la de fora, senão a paginação passa por acaso.
        repo = _repo(_form(updated_at=50), *forms)

        visto = []
        cursor = None
        paginas = 0
        while True:
            extra = {"updated_after": 100, "limit": 2}
            if cursor is not None:
                extra["exclusive_start_key"] = cursor
            response = _call(repo, **extra)
            visto.extend(f["id"] for f in response.body["forms"])
            cursor = response.body["last_evaluated_key"]
            paginas += 1
            if cursor is None:
                break

        assert paginas == 3
        assert visto == [f.id for f in forms]


class TestMineDelta:
    def test_mine_com_delta_filtra_pelo_instante_e_devolve_o_formulario_completo(self):
        meu_antigo = _form(updated_at=50, owner=REQUESTER_SUB)
        meu_novo = _form(updated_at=300, owner=REQUESTER_SUB)
        dos_outros = _form(updated_at=400, owner=OTHER_SUB)
        repo = _repo(meu_antigo, meu_novo, dos_outros)

        response = _call(repo, scope="mine", updated_after=100)

        assert response.status_code == 200
        assert [f["id"] for f in response.body["forms"]] == [meu_novo.id]
        assert "removed_from_pool" not in response.body["forms"][0]


class TestRegressaoSemDelta:
    def test_sem_updated_after_o_corpo_tem_so_as_chaves_de_hoje(self):
        repo = _repo(_form(updated_at=200), _form(updated_at=300))

        response = _call(repo)

        assert response.status_code == 200
        # `server_time` passou a vir em toda resposta (INF-SRVTIME); o resto do corpo continua o de hoje.
        assert set(response.body.keys()) == {"forms", "limit", "last_evaluated_key", "server_time"}
        assert len(response.body["forms"]) == 2
        for form in response.body["forms"]:
            assert "removed_from_pool" not in form
        corpo = {k: v for k, v in response.body.items() if k != "server_time"}
        # Referência: a viewmodel de hoje, sem os argumentos do delta, sobre os mesmos formulários.
        referencia = GetAllFormsViewmodel(forms=repo.forms, limit=POOL_DEFAULT_LIMIT, last_evaluated_key=None).to_dict()
        assert corpo == {k: v for k, v in referencia.items() if k != "server_time"}

    def test_sem_updated_after_ha_server_time_inteiro(self):
        response = _call(_repo(_form(updated_at=200)))

        assert isinstance(response.body["server_time"], int)


class TestServerTime:
    def test_com_delta_o_server_time_vem_e_fica_entre_antes_e_depois_da_consulta(self):
        repo = _repo(_form(updated_at=200))
        antes = int(time.time() * 1000)

        response = _call(repo, updated_after=100)

        depois = int(time.time() * 1000)
        assert antes <= response.body["server_time"] <= depois


class TestValidacaoDoDelta:
    def test_updated_after_negativo_e_400(self):
        response = _call(_repo(), updated_after=-1)

        assert response.status_code == 400
        assert "updated_after" in response.body

    def test_updated_after_nao_numerico_e_400(self):
        response = _call(_repo(), updated_after="abc")

        assert response.status_code == 400

    def test_scope_all_com_updated_after_e_400(self):
        response = _call(_repo(), scope="all", updated_after=100)

        assert response.status_code == 400

    def test_search_com_updated_after_e_400(self):
        response = _call(_repo(), updated_after=100, search="algo")

        assert response.status_code == 400
