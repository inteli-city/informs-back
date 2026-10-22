import os
import sys
import time

sys.path.append(os.getcwd())

from src.modules.sync_forms_origin.app.sync_forms_origin_usecase import SyncFormsOriginUsecase
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.origin_repository_mock import OriginRepositoryMock
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock
from src.shared.infra.repositories.sync_state_repository_mock import SyncStateRepositoryMock
from src.shared.known_systems import KNOWN_SYSTEMS, SYSTEM_TO_ORIGIN


def test_known_systems_inclui_uberlandia_com_origem_propria():
    assert SYSTEM_TO_ORIGIN["UBERLANDIA"] == "uberlandia"
    assert "UBERLANDIA" in KNOWN_SYSTEMS


def test_sync_envia_formulario_de_uberlandia_com_a_origem_uberlandia():
    now = int(time.time() * 1000)
    form_repo = FormRepositoryMock()
    for form in form_repo.forms:
        form.system = "UBERLANDIA"
        form.updated_at = now - 1000
    origin_repo = OriginRepositoryMock()
    usecase = SyncFormsOriginUsecase(
        form_repo=form_repo,
        origin_repo=origin_repo,
        sync_state_repo=SyncStateRepositoryMock(),
        sync_error_form_repo=SyncErrorFormRepositoryMock(),
    )

    results = usecase(
        systems=["UBERLANDIA"],
        system_mapping=SYSTEM_TO_ORIGIN,
        bootstrap_window_minutes=10,
        page_size=100,
    )

    assert results[0].system == "UBERLANDIA"
    assert origin_repo.sent, "o laço do sync precisa chegar ao repositório de origem"
    assert all(origin_system == "uberlandia" for origin_system, _, _ in origin_repo.sent)
