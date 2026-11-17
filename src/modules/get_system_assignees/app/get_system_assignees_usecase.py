from dataclasses import dataclass
from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.assignment_option_enum import AssignmentOption
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


@dataclass(frozen=True)
class Assignee:
    membership: SystemMembership
    profile: Profile


@dataclass(frozen=True)
class SystemAssignees:
    groups: List[SystemGroup]
    users: List[Assignee]
    # Só grupo (sem pessoa) cria formulário sem responsável, no pool do grupo:
    # o sistema precisa aceitar formulário sem responsável.
    allows_group_only: bool


class GetSystemAssigneesUsecase:
    """
    Para quem dá para criar um formulário no sistema: os grupos e as pessoas
    ativas (com os grupos de cada uma), para os campos "Grupo" e "Pessoa" da
    criação. Pode quem cria formulário com a opção "grupo e/ou pessoa" ligada
    no papel.

    Não devolve quem pergunta (para si é outra opção) nem e-mail: só o que a
    tela mostra.
    """

    def __init__(
        self,
        access_control: AccessControl,
        profile_repo: IProfileRepository,
        group_repo: ISystemGroupRepository,
        system_config_repo: Optional[ISystemConfigRepository] = None,
    ):
        self.access_control = access_control
        self.profile_repo = profile_repo
        self.group_repo = group_repo
        self.system_config_repo = system_config_repo

    def __call__(self, requester_user_id: str, system: str) -> SystemAssignees:
        access = self.access_control.access_in(requester_user_id, system)
        if Action.FORMS_CREATE not in access.actions or not access.allows(AssignmentOption.TARGETED):
            raise ForbiddenAction("Seu perfil não cria formulário para grupo ou pessoa neste sistema")

        users = []
        for membership in self.profile_repo.list_memberships_by_system(system):
            if membership.user_id == requester_user_id:
                continue
            profile = self.profile_repo.get_by_user_id(membership.user_id)
            if profile is None or not profile.active:
                continue
            users.append(Assignee(membership=membership, profile=profile))

        return SystemAssignees(
            groups=sorted(self.group_repo.list_groups(system), key=lambda group: group.name.casefold()),
            users=sorted(users, key=lambda user: (user.profile.name or "").casefold()),
            allows_group_only=self._allows_unassigned_forms(system),
        )

    def _allows_unassigned_forms(self, system: str) -> bool:
        if self.system_config_repo is None:
            return False
        config = self.system_config_repo.get_by_system(system)
        return bool(config and config.allow_unassigned_forms)
