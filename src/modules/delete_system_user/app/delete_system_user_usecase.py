from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can, ensure_no_escalation
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound


class DeleteSystemUserUsecase:
    """
    Tira o vínculo da pessoa com o sistema. Mesmas regras do PUT: precisa de
    `users.manage`, tirar ADMIN é só do super admin e quem não é ADMIN do
    sistema não mexe em quem tem ações que ele não tem.

    O acesso ao sistema vem do grupo do Cognito: se a pessoa continuar no
    grupo, no próximo login ela volta com o role padrão do sistema. Para
    tirar o acesso de vez, é no Cognito.
    """

    def __init__(self, access_control: AccessControl, profile_repo: IProfileRepository):
        self.access_control = access_control
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, system: str, target_user_id: str) -> None:
        ensure_can(self.access_control, requester_user_id, system, Action.USERS_MANAGE)

        current = self.profile_repo.get_membership(target_user_id, system)
        if current is None:
            raise NoItemsFound(f"Pessoa sem vínculo com o sistema {system}")
        if current.role_id == ADMIN_ROLE_ID and not self.access_control.is_super_admin(requester_user_id):
            raise ForbiddenAction("Só super admin dá ou tira o role ADMIN de um sistema")

        target_actions = self.access_control.access_in(target_user_id, system).actions
        ensure_no_escalation(self.access_control, requester_user_id, system, target_actions)

        self.profile_repo.delete_membership(target_user_id, system)
