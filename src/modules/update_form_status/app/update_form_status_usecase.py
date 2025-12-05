import datetime
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
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
        
        if status in [FORM_STATUS.CANCELLED, FORM_STATUS.COMPLETED]:
            raise ForbiddenAction("Não é possível alterar o status para cancelado ou concluído")

        if status == form.status:
            raise DuplicatedItem("O status do formulário já é o mesmo que o informado")
        
        if status is FORM_STATUS.NOT_STARTED and form.status is FORM_STATUS.IN_PROGRESS:
            start_date = None
        else:
            start_date = datetime.datetime.now().timestamp()
        
        return self.form_repository.update_form(user_id=user.user_id, form_id=form_id, status=status, in_progress_at=start_date)
        
