from collections import defaultdict

from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.sync_error_form_repository_interface import ISyncErrorFormRepository
from src.shared.helpers.errors.usecase_errors import NoItemsFound


class SyncFormsOriginCallbackUsecase:
    JOB_NAME = "sync_forms_origin"

    def __init__(self, form_repo: IFormRepository, sync_error_form_repo: ISyncErrorFormRepository):
        self.form_repo = form_repo
        self.sync_error_form_repo = sync_error_form_repo

    def __call__(self, form_ids: list, received_at: int) -> list[SyncErrorForm]:
        failed_form_ids = list(dict.fromkeys(form_ids))
        failures_by_system = defaultdict(list)
        missing_form_ids = []

        for form_id in failed_form_ids:
            form = self.form_repo.get_form_by_id(user_id="", form_id=form_id)
            if form is None:
                missing_form_ids.append(form_id)
                continue
            failures_by_system[form.system].append(form_id)

        if missing_form_ids:
            raise NoItemsFound(f"form_ids não encontrados: {', '.join(missing_form_ids)}")

        saved_error_forms: list[SyncErrorForm] = []
        for system, system_failed_items in failures_by_system.items():
            for form_id in system_failed_items:
                error_form = SyncErrorForm(
                    job_name=self.JOB_NAME,
                    system=system,
                    form_id=form_id,
                    source_updated_at=None,
                    last_failed_at=received_at,
                )
                self.sync_error_form_repo.upsert_error_form(error_form)
                saved_error_forms.append(error_form)

        return saved_error_forms
