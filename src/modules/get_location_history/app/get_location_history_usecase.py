from typing import List

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.domain.repositories.location_repository_interface import (
    ILocationRepository,
)
from src.shared.domain.repositories.profile_repository_interface import (
    IProfileRepository,
)
from src.shared.helpers.errors.controller_errors import WrongTypeParameter
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class GetLocationHistoryUsecase:
    """
    Lê o histórico de pings de um inspector (rota completa) na tabela
    Location. Apenas ADMIN ativo pode chamar.

    Regras:
    1. Requester precisa ser um ADMIN ativo (lookup no Profile).
    2. Range temporal precisa ser válido (since <= until).
    3. Range vazio retorna lista vazia (não é erro).
    """

    def __init__(
        self,
        location_repo: ILocationRepository,
        profile_repo: IProfileRepository,
    ):
        self.location_repo = location_repo
        self.profile_repo = profile_repo

    def __call__(
        self,
        *,
        requester_user_id: str,
        target_user_id: str,
        since_ms: int,
        until_ms: int,
    ) -> List[LocationPing]:
        self._ensure_requester_is_active_admin(requester_user_id)

        if since_ms > until_ms:
            raise WrongTypeParameter(
                "since",
                "<= until",
                "since > until (range temporal invertido)",
            )

        return self.location_repo.query_history(
            user_id=target_user_id,
            since_ms=since_ms,
            until_ms=until_ms,
        )

    def _ensure_requester_is_active_admin(self, requester_user_id: str) -> None:
        requester_profile = self.profile_repo.get_by_user_id(requester_user_id)
        if (
            requester_profile is None
            or not requester_profile.active
            or requester_profile.role != ProfileRole.ADMIN
        ):
            raise ForbiddenAction(
                "Apenas administradores ativos podem ler o histórico de tracking"
            )
