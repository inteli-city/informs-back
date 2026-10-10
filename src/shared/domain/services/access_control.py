from dataclasses import dataclass
from typing import FrozenSet, List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, ADMIN_ROLE_NAME
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository


ALL_ACTIONS: FrozenSet[Action] = frozenset(Action)


@dataclass(frozen=True)
class SystemAccess:
    """O que uma pessoa pode fazer em um sistema."""

    system: str
    role_id: Optional[str]
    role_name: Optional[str]
    actions: FrozenSet[Action]


class AccessControl:
    """
    A regra única de permissão. Uma pessoa pode uma ação em um sistema se:
      - é super admin (ativo); ou
      - tem o role ADMIN naquele sistema; ou
      - tem naquele sistema um role que inclui a ação.

    Perfil inexistente ou inativo não pode nada.
    """

    def __init__(self, profile_repo: IProfileRepository, role_repo: ISystemRoleRepository):
        self.profile_repo = profile_repo
        self.role_repo = role_repo

    def is_super_admin(self, user_id: str) -> bool:
        profile = self.profile_repo.get_by_user_id(user_id)
        return profile is not None and profile.is_active_super_admin()

    def is_system_admin(self, user_id: str, system: str) -> bool:
        return self.access_in(user_id, system).actions == ALL_ACTIONS

    def can(self, user_id: str, system: str, action: Action) -> bool:
        return action in self.access_in(user_id, system).actions

    def systems_where(self, user_id: str, action: Action) -> List[str]:
        """Sistemas em que a pessoa tem a ação pelo vínculo (não inclui o
        "todo sistema" do super admin — quem chama trata esse caso)."""
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile is None or not profile.active:
            return []
        return [
            membership.system
            for membership in self.profile_repo.get_memberships(user_id)
            if action in self._membership_access(membership).actions
        ]

    def systems_of(self, user_id: str) -> List[str]:
        """Sistemas em que a pessoa tem vínculo."""
        return [membership.system for membership in self.profile_repo.get_memberships(user_id)]

    def access_in(self, user_id: str, system: str) -> SystemAccess:
        profile = self.profile_repo.get_by_user_id(user_id)
        if profile is None or not profile.active:
            return SystemAccess(system=system, role_id=None, role_name=None, actions=frozenset())
        membership = self.profile_repo.get_membership(user_id, system)
        return self.resolve(profile, system, membership)

    def resolve(self, profile: Profile, system: str, membership: Optional[SystemMembership]) -> SystemAccess:
        """Acesso de um perfil já carregado (o login usa para não reler)."""
        if not profile.active:
            return SystemAccess(system=system, role_id=None, role_name=None, actions=frozenset())
        access = self._membership_access(membership) if membership else None
        if profile.super_admin:
            return SystemAccess(
                system=system,
                role_id=access.role_id if access else None,
                role_name=access.role_name if access else None,
                actions=ALL_ACTIONS,
            )
        return access or SystemAccess(system=system, role_id=None, role_name=None, actions=frozenset())

    def _membership_access(self, membership: SystemMembership) -> SystemAccess:
        if membership.role_id == ADMIN_ROLE_ID:
            return SystemAccess(
                system=membership.system, role_id=ADMIN_ROLE_ID, role_name=ADMIN_ROLE_NAME, actions=ALL_ACTIONS,
            )
        role = self.role_repo.get_role(membership.system, membership.role_id)
        if role is None:
            # Role apagado por fora: o vínculo fica sem efeito.
            return SystemAccess(system=membership.system, role_id=membership.role_id, role_name=None, actions=frozenset())
        return SystemAccess(
            system=membership.system, role_id=role.role_id, role_name=role.name, actions=frozenset(role.actions),
        )
