from typing import List

from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


class PutSystemUserGroupsUsecase:
    """
    Define os grupos de uma pessoa no sistema (ADR-0022), substituindo a lista
    anterior. Pode quem tem `users.manage` ali. Grupo não dá permissão nenhuma
    — só decide quais OS abertas a pessoa vê no pool —, por isso não passa
    pelas travas de escalada dos roles.
    """

    def __init__(
        self, access_control: AccessControl, group_repo: ISystemGroupRepository, profile_repo: IProfileRepository,
    ):
        self.access_control = access_control
        self.group_repo = group_repo
        self.profile_repo = profile_repo

    def __call__(self, requester_user_id: str, system: str, target_user_id: str, groups: List[str]) -> SystemMembership:
        ensure_can(self.access_control, requester_user_id, system, Action.USERS_MANAGE)

        current = self.profile_repo.get_membership(target_user_id, system)
        if current is None:
            raise NoItemsFound("A pessoa não tem vínculo com o sistema: dê um papel a ela antes")

        known = {group.group_id for group in self.group_repo.list_groups(system)}
        unknown = [group for group in dict.fromkeys(groups) if group not in known]
        if unknown:
            raise EntityError(f"grupo(s) inexistente(s) no sistema {system}: {', '.join(unknown)}")

        return self.profile_repo.put_membership(SystemMembership(
            user_id=current.user_id,
            system=current.system,
            role_id=current.role_id,
            created_at=current.created_at,
            updated_at=now_timestamp_ms(),
            groups=groups,
        ))
