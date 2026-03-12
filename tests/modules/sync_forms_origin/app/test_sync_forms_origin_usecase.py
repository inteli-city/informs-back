import os
import sys

sys.path.append(os.getcwd())

from src.modules.sync_forms_origin.app.sync_forms_origin_usecase import SyncFormsOriginUsecase
from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.entities.sync_state import SyncState
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.origin_repository_mock import OriginRepositoryMock
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock
from src.shared.infra.repositories.sync_state_repository_mock import SyncStateRepositoryMock


class SelectiveFailOriginRepository(OriginRepositoryMock):
    def __init__(self, fail_form_id: str):
        super().__init__()
        self.fail_form_id = fail_form_id

    def sync_forms(self, origin_system: str, payloads: list[dict], execution_id=None, logger=None):
        self.sent.append((origin_system, payloads, execution_id))
        form_ids = {payload.get("id") for payload in payloads}
        if self.fail_form_id in form_ids:
            return False, 500, "forced failure"
        return True, 200, "OK"


def test_sync_forms_origin_updates_sync_state_and_clears_pending_errors(monkeypatch):
    form_repo = FormRepositoryMock()
    state_repo = SyncStateRepositoryMock()
    error_repo = SyncErrorFormRepositoryMock()
    form_repo.forms[0].system = "GAIA"
    form_repo.forms[0].updated_at = 2000
    form_repo.forms[1].system = "GAIA"
    form_repo.forms[1].updated_at = 3000

    state_repo.set_state(
        SyncState(
            job_name="sync_forms_origin",
            system="GAIA",
            checkpoint_synced_at=1999,
            status="COMPLETED",
            execution_id="old-exec",
            started_at=1000,
            ended_at=1001,
            window_end=1001,
            updated_at=1001,
        )
    )

    # Simula erro pendente antigo para o mesmo form; deve ser removido quando sincronizar com sucesso.
    error_repo.upsert_error_form(
        SyncErrorForm(
            job_name="sync_forms_origin",
            system="GAIA",
            form_id=form_repo.forms[0].id,
            source_updated_at=2000,
            last_failed_at=1500,
        )
    )

    origin_repo = OriginRepositoryMock()
    usecase = SyncFormsOriginUsecase(
        form_repo=form_repo,
        origin_repo=origin_repo,
        sync_state_repo=state_repo,
        sync_error_form_repo=error_repo,
    )
    monkeypatch.setattr("src.modules.sync_forms_origin.app.sync_forms_origin_usecase.time.time", lambda: 4.0)

    results = usecase(
        systems=["GAIA"],
        system_mapping={"GAIA": "gaia"},
        bootstrap_window_minutes=10,
        page_size=100,
        logger=None,
    )

    assert len(results) == 1
    assert results[0].sent == 2
    assert results[0].failed == 0
    assert results[0].requests_made == 1
    assert results[0].status_code_counts == {"200": 1}
    assert results[0].response_tails_80_sample == ["OK"]
    assert results[0].previous_synced_at == 1999
    assert results[0].new_synced_at == 4000

    state = state_repo.get_state("sync_forms_origin", "GAIA")
    assert state is not None
    assert state.status == "COMPLETED"
    assert state.checkpoint_synced_at == 4000

    errors = error_repo.list_error_forms("sync_forms_origin", "GAIA")
    assert errors == []


def test_sync_forms_origin_bootstrap_window_when_state_missing(monkeypatch):
    form_repo = FormRepositoryMock()
    state_repo = SyncStateRepositoryMock()
    error_repo = SyncErrorFormRepositoryMock()
    form_repo.forms[0].system = "GAIA"
    form_repo.forms[0].updated_at = 3000
    form_repo.forms[1].system = "GAIA"
    form_repo.forms[1].updated_at = 5000

    origin_repo = OriginRepositoryMock()
    usecase = SyncFormsOriginUsecase(
        form_repo=form_repo,
        origin_repo=origin_repo,
        sync_state_repo=state_repo,
        sync_error_form_repo=error_repo,
    )
    monkeypatch.setattr("src.modules.sync_forms_origin.app.sync_forms_origin_usecase.time.time", lambda: 10.0)

    results = usecase(
        systems=["GAIA"],
        system_mapping={"GAIA": "gaia"},
        bootstrap_window_minutes=0,
        page_size=100,
        logger=None,
    )

    assert len(results) == 1
    assert results[0].previous_synced_at == 10000
    assert results[0].sync_started_at == 10001
    assert results[0].sent == 0
    assert results[0].requests_made == 0
    assert results[0].status_code_counts is None
    assert results[0].response_tails_80_sample is None
    assert results[0].new_synced_at == 10000

    state = state_repo.get_state("sync_forms_origin", "GAIA")
    assert state is not None
    assert state.checkpoint_synced_at == 10000


def test_sync_forms_origin_full_sync_when_state_missing_and_enabled(monkeypatch):
    form_repo = FormRepositoryMock()
    state_repo = SyncStateRepositoryMock()
    error_repo = SyncErrorFormRepositoryMock()
    form_repo.forms[0].system = "GAIA"
    form_repo.forms[0].updated_at = 3000
    form_repo.forms[1].system = "GAIA"
    form_repo.forms[1].updated_at = 5000

    origin_repo = OriginRepositoryMock()
    usecase = SyncFormsOriginUsecase(
        form_repo=form_repo,
        origin_repo=origin_repo,
        sync_state_repo=state_repo,
        sync_error_form_repo=error_repo,
    )
    monkeypatch.setattr("src.modules.sync_forms_origin.app.sync_forms_origin_usecase.time.time", lambda: 10.0)

    results = usecase(
        systems=["GAIA"],
        system_mapping={"GAIA": "gaia"},
        bootstrap_window_minutes=10,
        page_size=100,
        full_sync_on_first_run=True,
        logger=None,
    )

    assert len(results) == 1
    assert results[0].previous_synced_at == 0
    assert results[0].sync_started_at == 0
    assert results[0].sent == 2
    assert results[0].requests_made == 1
    assert results[0].status_code_counts == {"200": 1}
    assert results[0].response_tails_80_sample == ["OK"]
    assert results[0].new_synced_at == 10000

    state = state_repo.get_state("sync_forms_origin", "GAIA")
    assert state is not None
    assert state.checkpoint_synced_at == 10000


def test_sync_forms_origin_failure_marks_error_form_and_keeps_it_for_next_run(monkeypatch):
    form_repo = FormRepositoryMock()
    state_repo = SyncStateRepositoryMock()
    error_repo = SyncErrorFormRepositoryMock()
    form_repo.forms[0].system = "GAIA"
    form_repo.forms[0].updated_at = 2000
    form_repo.forms[1].system = "GAIA"
    form_repo.forms[1].updated_at = 3000

    state_repo.set_state(
        SyncState(
            job_name="sync_forms_origin",
            system="GAIA",
            checkpoint_synced_at=1999,
            status="COMPLETED",
            execution_id="old-exec",
            started_at=1000,
            ended_at=1001,
            window_end=1001,
            updated_at=1001,
        )
    )

    failing_origin_repo = SelectiveFailOriginRepository(fail_form_id=form_repo.forms[0].id)
    usecase = SyncFormsOriginUsecase(
        form_repo=form_repo,
        origin_repo=failing_origin_repo,
        sync_state_repo=state_repo,
        sync_error_form_repo=error_repo,
    )
    monkeypatch.setattr("src.modules.sync_forms_origin.app.sync_forms_origin_usecase.time.time", lambda: 4.0)

    results = usecase(
        systems=["GAIA"],
        system_mapping={"GAIA": "gaia"},
        bootstrap_window_minutes=10,
        page_size=1,
        logger=None,
    )

    assert len(results) == 1
    assert results[0].sent == 1
    assert results[0].failed == 1
    assert results[0].requests_made == 2
    assert results[0].status_code_counts == {"500": 1, "200": 1}
    assert results[0].response_tails_80_sample == ["forced failure", "OK"]
    assert results[0].new_synced_at == 4000

    state = state_repo.get_state("sync_forms_origin", "GAIA")
    assert state is not None
    assert state.checkpoint_synced_at == 4000

    errors = error_repo.list_error_forms("sync_forms_origin", "GAIA")
    assert len(errors) == 1
    assert errors[0].form_id == form_repo.forms[0].id
