from typing import List

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.location_repository_interface import (
    ILocationRepository,
)
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.controller_errors import WrongTypeParameter
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


class GetLocationHistoryUsecase:
    """
    Lê o histórico de pings de uma pessoa (rota completa) na tabela
    Location.

    Regras:
    1. Requester precisa ser super admin, ou ter `tracking.view` em algum
       sistema em que a pessoa alvo também tem vínculo.
    2. Range temporal precisa ser válido (since <= until).
    3. Range vazio retorna lista vazia (não é erro).
    """

    def __init__(
        self,
        location_repo: ILocationRepository,
        access_control: AccessControl,
    ):
        self.location_repo = location_repo
        self.access_control = access_control

    def __call__(
        self,
        *,
        requester_user_id: str,
        target_user_id: str,
        since_ms: int,
        until_ms: int,
    ) -> List[LocationPing]:
        self._ensure_requester_can_view(requester_user_id, target_user_id)

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

    def _ensure_requester_can_view(self, requester_user_id: str, target_user_id: str) -> None:
        if self.access_control.is_super_admin(requester_user_id):
            return
        viewer_systems = set(self.access_control.systems_where(requester_user_id, Action.TRACKING_VIEW))
        target_systems = set(self.access_control.systems_of(target_user_id))
        if not viewer_systems & target_systems:
            raise ForbiddenAction(
                "Usuário não pode ler o histórico de tracking desta pessoa"
            )
