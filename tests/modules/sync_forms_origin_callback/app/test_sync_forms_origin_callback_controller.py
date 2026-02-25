import os
import sys

sys.path.append(os.getcwd())

from src.modules.sync_forms_origin_callback.app.sync_forms_origin_callback_controller import (
    SyncFormsOriginCallbackController,
)
from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.helpers.external_interfaces.http_models import HttpRequest


class DummyUsecase:
    def __init__(self, output=None):
        self.output = output or [
            SyncErrorForm(
                job_name="sync_forms_origin",
                system="GAIA",
                form_id="form-1",
                source_updated_at=None,
                last_failed_at=123,
            ),
            SyncErrorForm(
                job_name="sync_forms_origin",
                system="GIPAV",
                form_id="form-2",
                source_updated_at=None,
                last_failed_at=123,
            ),
        ]
        self.received_failed_items = None
        self.received_at = None

    def __call__(self, form_ids, received_at):
        self.received_failed_items = form_ids
        self.received_at = received_at
        return self.output


class TestSyncFormsOriginCallbackController:
    def test_accepts_form_ids_payload(self):
        usecase = DummyUsecase()
        controller = SyncFormsOriginCallbackController(usecase=usecase)
        request = HttpRequest(body={"form_ids": ["form-1", "form-2"], "execution_id": "exec-123"})

        response = controller(request)

        assert response.status_code == 200
        assert response.body["received_count"] == 2
        assert "failed_count" not in response.body
        assert "failed_form_ids" not in response.body
        assert response.body["execution_id"] == "exec-123"
        assert usecase.received_failed_items == ["form-1", "form-2"]
        assert isinstance(usecase.received_at, int)
        assert response.body["saved_error_forms"][0]["job_name"] == "sync_forms_origin"

    def test_rejects_missing_form_ids(self):
        controller = SyncFormsOriginCallbackController(usecase=DummyUsecase())
        request = HttpRequest(body={})

        response = controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: form_ids"

    def test_rejects_empty_form_ids(self):
        controller = SyncFormsOriginCallbackController(usecase=DummyUsecase())
        request = HttpRequest(body={"form_ids": []})

        response = controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: form_ids"
