from typing import Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.possession_enum import Possession
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class GetFormUsecase:
    def __init__(self, form_repo: IFormRepository, access_control: Optional[AccessControl] = None):
        self.form_repo = form_repo
        self.access_control = access_control

    def __call__(self, requester_user_id: str, form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)

        if form is None:
            raise NoItemsFound("Formulário não encontrado")

        # OS aberta no pool (§6.3, especificação Uberlândia): leitura livre pra
        # qualquer usuário do sistema, salvo quando ela é de grupos em que a
        # pessoa não está (ADR-0022). Direcionada continua só pro dono.
        if form.possession is Possession.OWNED and form.user_id != requester_user_id:
            raise ForbiddenAction("Usuário não é o preenchedor deste formulário")

        if form.possession is Possession.OPEN and not self._can_see_open_form(requester_user_id, form):
            raise ForbiddenAction("Formulário destinado a um grupo em que você não está")

        return form

    def _can_see_open_form(self, requester_user_id: str, form: Form) -> bool:
        if not form.groups or self.access_control is None:
            return True
        if form.is_open_to_groups(self.access_control.groups_in(requester_user_id, form.system)):
            return True
        # Quem vê "Todas" abre a ficha de qualquer OS do sistema.
        return self.access_control.can(requester_user_id, form.system, Action.FORMS_VIEW_ALL)
