from datetime import datetime, timezone
from src.shared.domain.entities.form import Form
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.queue_repository_interface import IQueueRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class StartFormUsecase:
    def __init__(self, form_repo: IFormRepository, queue_repo: IQueueRepository):
        self.form_repo = form_repo
        self.queue_repo = queue_repo

    def __call__(self, requester_user_id: str, form_id: str, in_progress_at: int) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")

        if form.user_id != requester_user_id:
            raise ForbiddenAction("Usuário não é o preenchedor deste formulário")

        updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)

        form.start(in_progress_at=in_progress_at, updated_at=updated_at)

        updated_form = self.form_repo.update_form(
            user_id=requester_user_id,
            form_id=form_id,
            status=form.status,
            in_progress_at=form.in_progress_at,
            updated_at=form.updated_at,
        )

        self.queue_repo.send_form(updated_form)
