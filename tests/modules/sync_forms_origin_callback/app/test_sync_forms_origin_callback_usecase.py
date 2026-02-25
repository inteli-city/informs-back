import os
import sys

sys.path.append(os.getcwd())
import pytest

from src.modules.sync_forms_origin_callback.app.sync_forms_origin_callback_usecase import (
    SyncFormsOriginCallbackUsecase,
)
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock
from src.shared.helpers.errors.usecase_errors import NoItemsFound


class TestSyncFormsOriginCallbackUsecase:
    def test_persists_last_failure_snapshot_by_system(self):
        form_repo = FormRepositoryMock()
        repo = SyncErrorFormRepositoryMock()
        usecase = SyncFormsOriginCallbackUsecase(form_repo=form_repo, sync_error_form_repo=repo)

        gaia_form_id = form_repo.forms[0].id
        gipav_form_id = form_repo.forms[1].id
        form_repo.forms[1].system = "GIPAV"

        result = usecase(
            form_ids=[gaia_form_id, gipav_form_id],
            received_at=123456,
        )

        assert len(result) == 2
        assert sorted([item.system for item in result]) == ["GAIA", "GIPAV"]
        assert sorted([item.form_id for item in result]) == sorted([gaia_form_id, gipav_form_id])
        assert all(item.job_name == "sync_forms_origin" for item in result)
        assert all(item.last_failed_at == 123456 for item in result)

        gaia_errors = repo.list_error_forms("sync_forms_origin", "GAIA")
        assert len(gaia_errors) == 1
        assert gaia_errors[0].form_id == gaia_form_id
        assert gaia_errors[0].last_failed_at == 123456

        gipav_errors = repo.list_error_forms("sync_forms_origin", "GIPAV")
        assert len(gipav_errors) == 1
        assert gipav_errors[0].form_id == gipav_form_id

    def test_overwrites_previous_last_failure_snapshot_for_same_system(self):
        form_repo = FormRepositoryMock()
        repo = SyncErrorFormRepositoryMock()
        usecase = SyncFormsOriginCallbackUsecase(form_repo=form_repo, sync_error_form_repo=repo)
        gaia_form_id_1 = form_repo.forms[0].id
        gaia_form_id_2 = form_repo.forms[1].id

        usecase(
            form_ids=[gaia_form_id_1],
            received_at=111,
        )
        usecase(
            form_ids=[gaia_form_id_2],
            received_at=222,
        )

        errors = repo.list_error_forms("sync_forms_origin", "GAIA")
        stored_ids = sorted([item.form_id for item in errors])
        assert stored_ids == sorted([gaia_form_id_1, gaia_form_id_2])

    def test_raises_not_found_when_form_id_does_not_exist(self):
        form_repo = FormRepositoryMock()
        repo = SyncErrorFormRepositoryMock()
        usecase = SyncFormsOriginCallbackUsecase(form_repo=form_repo, sync_error_form_repo=repo)

        with pytest.raises(NoItemsFound) as err:
            usecase(
                form_ids=["form-inexistente"],
                received_at=333,
            )
        assert "form_ids não encontrados" in str(err.value)
