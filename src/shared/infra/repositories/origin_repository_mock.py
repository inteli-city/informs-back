from typing import List, Optional, Tuple

from src.shared.domain.repositories.origin_repository_interface import IOriginRepository


class OriginRepositoryMock(IOriginRepository):
    def __init__(self):
        self.sent: List[tuple] = []

    def sync_forms(
        self,
        origin_system: str,
        payloads: list[dict],
        execution_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> Tuple[bool, int, str]:
        self.sent.append((origin_system, payloads, execution_id))
        return True, 200, "OK"
