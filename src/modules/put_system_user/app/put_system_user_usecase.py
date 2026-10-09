from dataclasses import dataclass

from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, ADMIN_ROLE_NAME
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can, ensure_no_escalation
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


@dataclass(frozen=True)
class SystemUserSaved:
    membership: SystemMembership
    role_name: str


class PutSystemUserUsecase:
    """
    Dá ou troca o role de uma pessoa no sistema. Regras:
      - precisa de `users.manage` no sistema;
      - dar ou tirar o role ADMIN é só do super admin;
      - quem não é ADMIN do sistema não dá role com ações que não tem, nem
        mexe em quem tem ações que ele não tem;
      - a pessoa precisa ter perfil (entrou no app ao menos uma vez).
    """

    def __init__(
        self, access_control: AccessControl, profile_repo: IProfileRepository, role_repo: ISystemRoleRepository,
    ):
        self.access_control = access_control
        self.profile_repo = profile_repo
        self.role_repo = role_repo

    def __call__(self, requester_user_id: str, system: str, target_user_id: str, role_id: str) -> SystemUserSaved:
        ensure_can(self.access_control, requester_user_id, system, Action.USERS_MANAGE)

        if self.profile_repo.get_by_user_id(target_user_id) is None:
            raise NoItemsFound("Perfil não encontrado: a pessoa precisa entrar no app uma vez antes")

        current = self.profile_repo.get_membership(target_user_id, system)
        touches_admin = role_id == ADMIN_ROLE_ID or (current is not None and current.role_id == ADMIN_ROLE_ID)
        if touches_admin and not self.access_control.is_super_admin(requester_user_id):
            raise ForbiddenAction("Só super admin dá ou tira o role ADMIN de um sistema")

        role_name = ADMIN_ROLE_NAME
        if role_id != ADMIN_ROLE_ID:
            role = self.role_repo.get_role(system, role_id)
            if role is None:
                raise NoItemsFound(f"Role {role_id} não encontrado no sistema {system}")
            role_name = role.name
            target_actions = self.access_control.access_in(target_user_id, system).actions
            ensure_no_escalation(self.access_control, requester_user_id, system, [*role.actions, *target_actions])

        now_ms = now_timestamp_ms()
        membership = self.profile_repo.put_membership(SystemMembership(
            user_id=target_user_id,
            system=system,
            role_id=role_id,
            created_at=current.created_at if current else now_ms,
            updated_at=now_ms,
        ))
        return SystemUserSaved(membership=membership, role_name=role_name)
