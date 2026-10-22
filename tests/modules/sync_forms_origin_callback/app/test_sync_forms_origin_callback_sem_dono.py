import os
import sys

sys.path.append(os.getcwd())

from src.modules.sync_forms_origin_callback.app.sync_forms_origin_callback_usecase import (
    SyncFormsOriginCallbackUsecase,
)
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock


def test_callback_registra_erro_de_formulario_sem_dono():
    # Formulário sem user_id: o callback não olha dono (o pool de formulários é aberto para o
    # sync). O erro precisa ser registrado do mesmo jeito, sem depender de quem criou o formulário.
    form_repo = FormRepositoryMock()
    form = form_repo.forms[0]
    form.user_id = None
    form.system = "UBERLANDIA"
    error_repo = SyncErrorFormRepositoryMock()
    usecase = SyncFormsOriginCallbackUsecase(form_repo=form_repo, sync_error_form_repo=error_repo)

    result = usecase(form_ids=[form.id], received_at=123)

    assert len(result) == 1
    assert result[0].system == "UBERLANDIA"
    assert result[0].form_id == form.id
    saved = error_repo.list_error_forms("sync_forms_origin", "UBERLANDIA")
    assert [item.form_id for item in saved] == [form.id]
