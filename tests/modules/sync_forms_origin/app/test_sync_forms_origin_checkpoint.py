import copy
import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.modules.sync_forms_origin.app.sync_forms_origin_usecase import SyncFormsOriginUsecase
from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.entities.sync_state import SyncState
from src.shared.infra.dtos.sync_state_dynamo_dto import SyncStateDynamoDTO
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.origin_repository_mock import OriginRepositoryMock
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock
from src.shared.infra.repositories.sync_state_repository_mock import SyncStateRepositoryMock

JOB = "sync_forms_origin"
NOW_S = 10_000_000.0
NOW_MS = int(NOW_S * 1000)
PAGE = 100


def _forms(updated_ats):
    base = FormRepositoryMock().forms[0]
    out = []
    for ts in updated_ats:
        form = copy.deepcopy(base)
        form.id = str(uuid.uuid4())
        form.system = "GAIA"
        form.updated_at = ts
        out.append(form)
    return out


class _FailingOrigin(OriginRepositoryMock):
    """Recusa o lote que contém `fail_form_id`, como o Apex faria com um formulário inválido."""

    def __init__(self, fail_form_id: str):
        super().__init__()
        self.fail_form_id = fail_form_id

    def sync_forms(self, origin_system, payloads, execution_id=None, logger=None):
        self.sent.append((origin_system, payloads, execution_id))
        if self.fail_form_id in {p.get("id") for p in payloads}:
            return False, 500, "forced failure"
        return True, 200, "OK"


def _sent_ids(origin: OriginRepositoryMock) -> list:
    return [payload["id"] for _, payloads, _ in origin.sent for payload in payloads]


class _World:
    """Repositórios compartilhados entre as execuções de uma mesma sincronização."""

    def __init__(self, forms):
        self.form_repo = FormRepositoryMock()
        self.form_repo.forms = forms
        self.state_repo = SyncStateRepositoryMock()
        self.error_repo = SyncErrorFormRepositoryMock()

    def run(self, origin, remaining_time_ms=None, page_size=PAGE, full_sync_on_first_run=True):
        usecase = SyncFormsOriginUsecase(
            form_repo=self.form_repo,
            origin_repo=origin,
            sync_state_repo=self.state_repo,
            sync_error_form_repo=self.error_repo,
        )
        results = usecase(
            systems=["GAIA"],
            system_mapping={"GAIA": "gaia"},
            bootstrap_window_minutes=10,
            page_size=page_size,
            full_sync_on_first_run=full_sync_on_first_run,
            remaining_time_ms=remaining_time_ms,
        )
        return results[0]

    def state(self) -> SyncState:
        return self.state_repo.get_state(JOB, "GAIA")


def _patch_clock(monkeypatch):
    monkeypatch.setattr("src.modules.sync_forms_origin.app.sync_forms_origin_usecase.time.time", lambda: NOW_S)


def _stop_after_sends(origin, count):
    """Pouco tempo restante assim que `count` lotes foram enviados por `origin`."""
    return lambda: 0 if len(origin.sent) >= count else 10**9


# 1. Retomada exata: a execução para no meio; a seguinte manda exatamente o resto.
def test_retomada_manda_exatamente_o_que_faltou(monkeypatch):
    _patch_clock(monkeypatch)
    forms = _forms([1000 + i for i in range(250)])
    world = _World(forms)

    origin1 = OriginRepositoryMock()
    world.run(origin1, remaining_time_ms=_stop_after_sends(origin1, 1))
    origin2 = OriginRepositoryMock()
    world.run(origin2)

    enviados = _sent_ids(origin1) + _sent_ids(origin2)
    assert len(enviados) == 250
    assert len(set(enviados)) == 250
    assert set(enviados) == {form.id for form in forms}


# 2. Empate de updated_at no corte do lote: nada se perde nem se repete.
def test_empate_de_updated_at_no_corte_nao_perde_nem_repete(monkeypatch):
    _patch_clock(monkeypatch)
    forms = _forms([1000] * 150 + [1001] * 100)
    world = _World(forms)

    origin1 = OriginRepositoryMock()
    world.run(origin1, remaining_time_ms=_stop_after_sends(origin1, 1))
    origin2 = OriginRepositoryMock()
    world.run(origin2)

    enviados = _sent_ids(origin1) + _sent_ids(origin2)
    assert len(enviados) == len(set(enviados)) == 250
    assert set(enviados) == {form.id for form in forms}


# 3. Parada graciosa: para depois do lote em curso, sem marcar o fim da janela.
def test_parada_graciosa_nao_avanca_o_checkpoint_para_o_fim(monkeypatch):
    _patch_clock(monkeypatch)
    forms = _forms([1000 + i for i in range(250)])
    world = _World(forms)
    origin = OriginRepositoryMock()

    result = world.run(origin, remaining_time_ms=lambda: 30_000)

    assert len(_sent_ids(origin)) == PAGE
    assert result.partial is True
    state = world.state()
    assert state.checkpoint_synced_at != NOW_MS
    assert state.status == "COMPLETED"
    assert state.progress_updated_at is not None
    assert state.progress_form_id is not None


# 4. Fim normal: esgotando as páginas, o checkpoint vai para o fim e a tabela de erros é repetida.
def test_fim_normal_avanca_checkpoint_e_repete_a_tabela_de_erros(monkeypatch):
    _patch_clock(monkeypatch)
    depois_da_janela = _forms([NOW_MS + 1])[0]
    forms = _forms([1000 + i for i in range(250)]) + [depois_da_janela]
    world = _World(forms)
    world.error_repo.upsert_error_form(SyncErrorForm(
        job_name=JOB, system="GAIA", form_id=depois_da_janela.id,
        source_updated_at=depois_da_janela.updated_at, last_failed_at=1,
    ))
    origin = OriginRepositoryMock()

    result = world.run(origin, remaining_time_ms=lambda: 10**9)

    assert result.partial is False
    state = world.state()
    assert state.checkpoint_synced_at == NOW_MS
    assert state.status == "COMPLETED"
    assert state.progress_updated_at is None
    assert state.progress_form_id is None
    assert depois_da_janela.id in _sent_ids(origin)
    assert world.error_repo.list_error_forms(JOB, "GAIA") == []


# 5. Falha de lote: o formulário vai para a tabela de erros, a execução segue, e o checkpoint do lote avança.
def test_falha_de_lote_vai_para_a_tabela_de_erros_e_a_execucao_segue(monkeypatch):
    _patch_clock(monkeypatch)
    a, b, c = _forms([1000, 1001, 1002])
    world = _World([a, b, c])
    origin = _FailingOrigin(fail_form_id=c.id)

    result = world.run(origin, page_size=2)

    assert result.failed == 1
    assert [e.form_id for e in world.error_repo.list_error_forms(JOB, "GAIA")] == [c.id]
    assert world.state().checkpoint_synced_at == NOW_MS
    assert world.state().status == "COMPLETED"


# 5b. Lote que falhou também avança o checkpoint por lote: a retomada não o manda de novo, e a tabela de erros o refaz.
def test_lote_que_falhou_avanca_o_checkpoint_e_a_tabela_refaz(monkeypatch):
    _patch_clock(monkeypatch)
    a, b, c, d = _forms([1000, 1001, 1002, 1003])
    world = _World([a, b, c, d])
    # Lote de 1: o lote de `c` falha sozinho, e a execução para logo depois dele (3 envios: a, b, c).
    origin1 = _FailingOrigin(fail_form_id=c.id)
    world.run(origin1, page_size=1, remaining_time_ms=_stop_after_sends(origin1, 3))

    origin2 = OriginRepositoryMock()
    world.run(origin2, page_size=1)

    # Retomada manda `d` (o que vem depois do progresso); `c` volta pela tabela de erros, no fim.
    assert _sent_ids(origin2) == [d.id, c.id]
    assert world.error_repo.list_error_forms(JOB, "GAIA") == []


# 6. Compatibilidade: estado antigo, sem os campos novos, continua do checkpoint como antes.
def test_estado_antigo_sem_progresso_continua_do_checkpoint(monkeypatch):
    _patch_clock(monkeypatch)
    antes = _forms([4000])[0]
    depois = _forms([6000])[0]
    world = _World([antes, depois])
    world.state_repo.set_state(SyncState(
        job_name=JOB, system="GAIA", checkpoint_synced_at=5000, status="COMPLETED",
        execution_id="antiga", started_at=1, ended_at=2, window_end=5000, updated_at=2,
    ))
    origin = OriginRepositoryMock()

    world.run(origin, full_sync_on_first_run=False)

    assert _sent_ids(origin) == [depois.id]


def test_dto_sem_os_campos_novos_le_progresso_nulo_e_ida_e_volta_preserva():
    item = {
        "checkpoint_synced_at": 5000, "status": "COMPLETED", "execution_id": "e",
        "started_at": 1, "ended_at": 2, "window_end": 5000, "updated_at": 2,
    }
    lido = SyncStateDynamoDTO.from_dynamo(dict(item, PK="sync_state#sync_forms_origin#GAIA")).to_entity()
    assert lido.progress_updated_at is None
    assert lido.progress_form_id is None

    com_progresso = SyncState(
        job_name=JOB, system="GAIA", checkpoint_synced_at=5000, status="RUNNING", execution_id="e",
        started_at=1, ended_at=None, window_end=5000, updated_at=2,
        progress_updated_at=1234, progress_form_id="abc",
    )
    gravado = SyncStateDynamoDTO.from_entity(com_progresso).to_dynamo()
    relido = SyncStateDynamoDTO.from_dynamo(dict(gravado, PK="sync_state#sync_forms_origin#GAIA")).to_entity()
    assert relido.progress_updated_at == 1234
    assert relido.progress_form_id == "abc"


# Sem `remaining_time_ms` (teste, execução local), nunca há parada graciosa.
def test_sem_tempo_restante_nunca_para_parcial(monkeypatch):
    _patch_clock(monkeypatch)
    world = _World(_forms([1000 + i for i in range(250)]))

    result = world.run(OriginRepositoryMock())

    assert result.partial is False
    assert world.state().checkpoint_synced_at == NOW_MS
