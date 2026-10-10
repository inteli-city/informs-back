from src.shared.domain.entities.system_role import ADMIN_ROLE_ID
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can, ensure_no_escalation
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound


class DeleteSystemRoleUsecase:
    """
    Apaga um role do sistema. Recusa (409) se:
      - é o role padrão (quem entrasse no sistema ficaria sem role);
      - alguém ainda tem o role (trocar o role dessas pessoas antes).
    O ADMIN é fixo e não se apaga.
    """

    def __init__(
        self, access_control: AccessControl, role_repo: ISystemRoleRepository, profile_repo: IProfileRepository,
    ):
        self.access_control = access_control
        self.role_repo = role_repo
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, system: str, role_id: str) -> None:
        ensure_can(self.access_control, requester_user_id, system, Action.ROLES_MANAGE)
        if role_id == ADMIN_ROLE_ID:
            raise ForbiddenAction("O role ADMIN é fixo e não pode ser apagado")

        role = self.role_repo.get_role(system, role_id)
        if role is None:
            raise NoItemsFound(f"Role {role_id} não encontrado no sistema {system}")
        ensure_no_escalation(self.access_control, requester_user_id, system, role.actions)

        if role.is_default:
            raise DuplicatedItem("É o role padrão do sistema: marque outro como padrão antes de apagar")
        in_use = self.profile_repo.count_memberships_by_role(system, role_id)
        if in_use:
            raise DuplicatedItem(f"Role em uso por {in_use} pessoa(s): troque o role delas antes de apagar")

        self.role_repo.delete_role(system, role_id)
