from typing import List

from src.shared.domain.enums.action_enum import Action


class GetPermissionActionsUsecase:
    """Catálogo fixo de ações — o que um role de sistema pode combinar. Não
    depende de quem pede: é a mesma lista para todo mundo."""

    def __call__(self) -> List[Action]:
        return list(Action)
