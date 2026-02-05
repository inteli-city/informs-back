from src.shared.domain.entities.form import Form
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class GetFormUsecase:
    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(self, requester_user_id: str, form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")

        if form.user_id != requester_user_id:
            raise ForbiddenAction("Usuário não é o preenchedor deste formulário")

        return form
