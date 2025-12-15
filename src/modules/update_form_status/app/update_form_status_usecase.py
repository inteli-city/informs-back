import datetime
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateFormStatusUsecase:
    def __init__(self, form_repository: IFormRepository):
        self.form_repository = form_repository

    def __call__(self, user: UserGatewayDTO, form_id: str, status: FORM_STATUS):
        
        form = self.form_repository.get_form_by_id(user_id=user.user_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        
        if form.system not in user.systems:
            raise ForbiddenAction("Usuário não tem permissão para alterar o status desse formulário")
        
        if user.user_id != form.user_id:
            raise ForbiddenAction("Usuário não pode alterar o status de um formulário não direcionado a ele")

        updated_at = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
        form.update_status(new_status=status, updated_at=updated_at)

        updated_form = self.form_repository.update_form(
            user_id=user.user_id,
            form_id=form_id,
            status=form.status,
            in_progress_at=form.in_progress_at,
            updated_at=form.updated_at
        )

        if updated_form is None:
            raise NoItemsFound("Formulário não encontrado")

        return updated_form
        
