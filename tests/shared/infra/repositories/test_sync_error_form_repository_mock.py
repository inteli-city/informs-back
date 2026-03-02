import os
import sys

sys.path.append(os.getcwd())

from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.infra.repositories.sync_error_form_repository_mock import SyncErrorFormRepositoryMock


def test_sync_error_form_repository_mock_upsert_list_delete():
    repo = SyncErrorFormRepositoryMock()

    item = SyncErrorForm(
        job_name="sync_forms_origin",
        system="GAIA",
        form_id="form-1",
        source_updated_at=123,
        last_failed_at=999,
    )
    repo.upsert_error_form(item)

    loaded = repo.list_error_forms("sync_forms_origin", "GAIA")
    assert len(loaded) == 1
    assert loaded[0].form_id == "form-1"

    repo.delete_error_forms("sync_forms_origin", "GAIA", ["form-1"])
    assert repo.list_error_forms("sync_forms_origin", "GAIA") == []
