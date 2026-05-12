from datetime import datetime, timezone
from typing import List, Tuple

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class LoginProfileUsecase:
    """
    Resolve o Profile do usuário autenticado:

    - Se já existir e estiver ativo: devolve `(profile, just_created=False)`.
    - Se já existir e estiver inativo: ForbiddenAction (admin desativou).
    - Se NÃO existir: auto-cria como INSPECTOR usando dados do Cognito,
      com o primeiro grupo (≠ FORMULARIOS) como `system`. Devolve
      `(profile, just_created=True)`.

    Premissa: o authorizer do API Gateway já validou o JWT (Cognito).
    Aqui só tratamos a camada aplicacional. Como apenas pessoas conhecidas
    têm acesso ao pool, o auto-create como INSPECTOR é seguro.
    """

    def __init__(self, profile_repo: IProfileRepository):
        self.profile_repo = profile_repo

    def __call__(
        self,
        user_id: str,
        name: str,
        email: str,
        cognito_systems: List[str],
    ) -> Tuple[Profile, bool]:
        existing = self.profile_repo.get_by_user_id(user_id)
        if existing is not None:
            if not existing.active:
                raise ForbiddenAction("Perfil desativado — contate um administrador")
            return existing, False

        return self._auto_create_inspector(
            user_id=user_id,
            name=name,
            email=email,
            cognito_systems=cognito_systems,
        )

    def _auto_create_inspector(
        self,
        user_id: str,
        name: str,
        email: str,
        cognito_systems: List[str],
    ) -> Tuple[Profile, bool]:
        # UserGatewayDTO já remove "FORMULARIOS" da lista de systems (é só
        # gate de entrada, não é "sistema" no nosso domínio). Então aqui
        # `cognito_systems` chega sem ele.
        if not cognito_systems:
            raise ForbiddenAction(
                "Usuário Cognito não pertence a nenhum sistema (apenas FORMULARIOS é insuficiente)"
            )
        chosen_system = cognito_systems[0]

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        profile = Profile(
            user_id=user_id,
            role=PROFILE_ROLE.INSPECTOR,
            name=name,
            email=email,
            system=chosen_system,
            vehicle_plate=None,
            active=True,
            created_at=now_ms,
            updated_at=now_ms,
        )
        created = self.profile_repo.create(profile)
        return created, True
