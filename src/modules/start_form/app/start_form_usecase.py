from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class StartFormUsecase:
    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(self, requester_user_id: str, form_id: str, in_progress_at: int) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")

        form.ensure_assigned_to(requester_user_id, "Usuário não é o preenchedor deste formulário")

        updated_at = now_timestamp_ms()

        form.start(in_progress_at=in_progress_at, updated_at=updated_at)

        updated_form = self.form_repo.update_form(
            user_id=requester_user_id,
            form_id=form_id,
            status=form.status,
            in_progress_at=form.in_progress_at,
            updated_at=form.updated_at,
            expected_status=FormStatus.PENDING,
        )
        return updated_form
