from typing import List, Optional, Tuple

from src.shared.domain.repositories.origin_repository_interface import IOriginRepository


class OriginRepositoryMock(IOriginRepository):
    def __init__(self):
        self.sent: List[tuple] = []

    def sync_form(self, origin_system: str, payload: dict, logger: Optional[object] = None) -> Tuple[bool, int, str]:
        self.sent.append((origin_system, payload))
        return True, 200, "OK"
