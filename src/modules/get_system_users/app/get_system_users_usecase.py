from dataclasses import dataclass
from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, ADMIN_ROLE_NAME
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can


@dataclass(frozen=True)
class SystemUser:
    membership: SystemMembership
    profile: Optional[Profile]
    role_name: Optional[str]


class GetSystemUsersUsecase:
    """Pessoas com vínculo no sistema e o role de cada uma. Pode quem tem
    `users.manage` ali."""

    def __init__(
        self, access_control: AccessControl, profile_repo: IProfileRepository, role_repo: ISystemRoleRepository,
    ):
        self.access_control = access_control
        self.profile_repo = profile_repo
        self.role_repo = role_repo

    def __call__(self, requester_user_id: str, system: str) -> List[SystemUser]:
        ensure_can(self.access_control, requester_user_id, system, Action.USERS_MANAGE)

        role_names = {role.role_id: role.name for role in self.role_repo.list_roles(system)}
        role_names[ADMIN_ROLE_ID] = ADMIN_ROLE_NAME

        users = [
            SystemUser(
                membership=membership,
                profile=self.profile_repo.get_by_user_id(membership.user_id),
                role_name=role_names.get(membership.role_id),
            )
            for membership in self.profile_repo.list_memberships_by_system(system)
        ]
        return sorted(users, key=lambda user: (user.profile.name.casefold() if user.profile else ""))
