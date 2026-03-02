from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.helpers.contracts.endpoints.sync_origin_callback_contract import SyncCallbackResponseSchema


class SyncErrorFormViewmodel:
    def __init__(self, sync_error_form: SyncErrorForm):
        self.sync_error_form = sync_error_form

    def to_dict(self):
        return {
            "job_name": self.sync_error_form.job_name,
            "system": self.sync_error_form.system,
            "form_id": self.sync_error_form.form_id,
            "source_updated_at": self.sync_error_form.source_updated_at,
            "last_failed_at": self.sync_error_form.last_failed_at,
        }


class SyncFormsOriginCallbackViewmodel:
    def __init__(
        self,
        form_ids: list[str],
        saved_error_forms: list[SyncErrorForm],
        received_at: int,
        execution_id: str | None = None,
    ):
        self.form_ids = form_ids
        self.saved_error_forms = saved_error_forms
        self.received_at = received_at
        self.execution_id = execution_id

    def to_dict(self):
        payload = {
            "received_count": len(self.form_ids),
            "saved_error_forms": [SyncErrorFormViewmodel(item).to_dict() for item in self.saved_error_forms],
            "received_at": self.received_at,
            "execution_id": self.execution_id,
            "message": "Callback completo!",
        }
        return SyncCallbackResponseSchema.model_validate(payload).model_dump(exclude_none=True)
