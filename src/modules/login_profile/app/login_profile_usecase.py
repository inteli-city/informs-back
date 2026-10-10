from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl, SystemAccess
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


@dataclass(frozen=True)
class LoginResult:
    profile: Profile
    just_created: bool
    systems: List[SystemAccess]


class LoginProfileUsecase:
    """
    Resolve o Profile do usuário autenticado e o que ele pode em cada sistema:

    - Perfil inativo: ForbiddenAction (foi desativado).
    - Sem perfil: cria a pessoa com os dados do Cognito (`just_created=True`).
    - Para cada sistema do Cognito sem vínculo, cria o vínculo com o role
      padrão daquele sistema (se o sistema tiver um). Sistema sem role padrão
      fica sem vínculo: a pessoa acessa, mas sem nenhuma ação.

    Premissa: o authorizer do API Gateway já validou o JWT (Cognito). Como só
    pessoas conhecidas têm acesso ao pool, criar o perfil no login é seguro.
    """

    def __init__(self, profile_repo: IProfileRepository, role_repo: ISystemRoleRepository):
        self.profile_repo = profile_repo
        self.role_repo = role_repo
        self.access_control = AccessControl(profile_repo, role_repo)

    def __call__(self, user_id: str, name: str, email: str, cognito_systems: List[str]) -> LoginResult:
        profile = self.profile_repo.get_by_user_id(user_id)
        just_created = profile is None
        if profile is None:
            profile = self._create_profile(user_id, name, email, cognito_systems)
        elif not profile.active:
            raise ForbiddenAction("Perfil desativado — contate um administrador")

        memberships = {m.system: m for m in self.profile_repo.get_memberships(user_id)}
        for system in cognito_systems:
            if system not in memberships:
                created = self._join_with_default_role(user_id, system)
                if created is not None:
                    memberships[system] = created

        systems = [
            self.access_control.resolve(profile, system, memberships.get(system))
            for system in cognito_systems
        ]
        return LoginResult(profile=profile, just_created=just_created, systems=systems)

    def _create_profile(self, user_id: str, name: str, email: str, cognito_systems: List[str]) -> Profile:
        # UserGatewayDTO já remove "FORMULARIOS" da lista de systems (é só
        # gate de entrada, não é "sistema" no nosso domínio).
        if not cognito_systems:
            raise ForbiddenAction(
                "Usuário Cognito não pertence a nenhum sistema (apenas FORMULARIOS é insuficiente)"
            )
        now_ms = _now_ms()
        return self.profile_repo.create(Profile(
            user_id=user_id, name=name, email=email, active=True, created_at=now_ms, updated_at=now_ms,
        ))

    def _join_with_default_role(self, user_id: str, system: str) -> Optional[SystemMembership]:
        default_role = self._default_role(system)
        if default_role is None:
            return None
        now_ms = _now_ms()
        return self.profile_repo.put_membership(SystemMembership(
            user_id=user_id, system=system, role_id=default_role.role_id, created_at=now_ms, updated_at=now_ms,
        ))

    def _default_role(self, system: str) -> Optional[SystemRole]:
        return next((role for role in self.role_repo.list_roles(system) if role.is_default), None)


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)
