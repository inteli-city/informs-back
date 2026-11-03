import os
import sys
import uuid

sys.path.append(os.getcwd())
from src.modules.get_all_forms.app.get_all_forms_controller import GetAllFormsController
from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from tests.modules.access_fixtures import AccessScenario, give_role

SYSTEM = "GAIA"
CREATED_BY = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
MEU_GRUPO = "g-meu"
OUTRO_GRUPO = "g-outro"

justification = Justification(
    options=[JustificationOption(option='option', required_image=True, required_text=True)],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _form(updated_at: int, groups=None) -> Form:
    """OS aberta (sem dono, no pool). `groups` diz para quais grupos ela se destina."""
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    return Form(
        id=str(uuid.uuid4()), form_title='TITULO SECRETO', created_by=CREATED_BY,
        user_id=None, system=SYSTEM, street='RUA SECRETA', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=updated_at,
        justification=justification, sections=[Section(section_id=1, fields=[text_field])],
        groups=groups,
    )


def _pessoa(scenario: AccessScenario, user_id: str, groups: list) -> None:
    """Pessoa com vínculo no GAIA e os grupos informados (sem role de ver tudo)."""
    scenario.add_person(user_id, "Pessoa de teste")
    scenario.profile_repo.put_membership(SystemMembership(
        user_id=user_id, system=SYSTEM, role_id="r-tecnico-gaia", created_at=1, updated_at=1, groups=groups,
    ))


def _delta(scenario: AccessScenario, repo: FormRepositoryMock, user_id: str):
    controller = GetAllFormsController(GetAllFormsUsecase(repo, scenario.access_control))
    request = HttpRequest(body={
        "requester_user": {"sub": user_id, "name": "Tester", "email": "t@example.com",
                           "cognito:groups": "FORMULARIOS,GAIA"},
        "scope": "pool",
        "system": SYSTEM,
        "updated_after": 100,
    })
    return controller(request)


CHAVES_DO_MARCADOR = {"id", "status", "possession", "updated_at", "removed_from_pool"}


class TestDeltaDoPoolRespeitaGrupos:
    def test_os_de_grupo_alheio_volta_so_como_marcador_nao_como_formulario(self):
        scenario = AccessScenario()
        user = "d61dbf66-a10f-11ed-a8fc-0242ac120101"
        _pessoa(scenario, user, [MEU_GRUPO])
        alheia = _form(updated_at=200, groups=[OUTRO_GRUPO])
        repo = FormRepositoryMock()
        repo.forms = [alheia]

        response = _delta(scenario, repo, user)

        assert response.status_code == 200
        item = response.body["forms"][0]
        assert set(item.keys()) == CHAVES_DO_MARCADOR
        assert item["removed_from_pool"] is True
        assert item["id"] == alheia.id
        assert "TITULO SECRETO" not in str(response.body)
        assert "RUA SECRETA" not in str(response.body)

    def test_quem_saiu_do_grupo_recebe_so_o_marcador(self):
        scenario = AccessScenario()
        user = "d61dbf66-a10f-11ed-a8fc-0242ac120102"
        _pessoa(scenario, user, [])
        repo = FormRepositoryMock()
        repo.forms = [_form(updated_at=200, groups=[MEU_GRUPO])]

        response = _delta(scenario, repo, user)

        item = response.body["forms"][0]
        assert set(item.keys()) == CHAVES_DO_MARCADOR
        assert "TITULO SECRETO" not in str(response.body)

    def test_os_do_meu_grupo_volta_completa(self):
        scenario = AccessScenario()
        user = "d61dbf66-a10f-11ed-a8fc-0242ac120103"
        _pessoa(scenario, user, [MEU_GRUPO])
        repo = FormRepositoryMock()
        repo.forms = [_form(updated_at=200, groups=[MEU_GRUPO])]

        response = _delta(scenario, repo, user)

        item = response.body["forms"][0]
        assert item["form_title"] == "TITULO SECRETO"
        assert "removed_from_pool" not in item

    def test_os_sem_grupo_volta_completa_para_qualquer_um(self):
        scenario = AccessScenario()
        user = "d61dbf66-a10f-11ed-a8fc-0242ac120104"
        _pessoa(scenario, user, [])
        repo = FormRepositoryMock()
        repo.forms = [_form(updated_at=200, groups=None)]

        response = _delta(scenario, repo, user)

        item = response.body["forms"][0]
        assert item["form_title"] == "TITULO SECRETO"
        assert "removed_from_pool" not in item

    def test_ver_tudo_nao_abre_o_pool_do_delta_como_nao_abre_a_listagem(self):
        # Mesmo critério da listagem do pool (#102): `forms.view_all` não passa por cima dos grupos.
        scenario = AccessScenario()
        user = "d61dbf66-a10f-11ed-a8fc-0242ac120105"
        scenario.add_person(user, "Gestora de tudo")
        give_role(scenario.profile_repo, scenario.role_repo, user, SYSTEM, [Action.FORMS_VIEW_ALL])
        repo = FormRepositoryMock()
        repo.forms = [_form(updated_at=200, groups=[OUTRO_GRUPO])]

        response = _delta(scenario, repo, user)

        assert set(response.body["forms"][0].keys()) == CHAVES_DO_MARCADOR
