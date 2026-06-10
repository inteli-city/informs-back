from typing import List, Optional, Tuple

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.functions.nearest_neighbor import (
    order_by_nearest_neighbor,
    total_route_distance_km,
)


class PlanRouteUsecase:
    """
    Stateless route planner.

    Para o `requester_user_id` informado, busca todos os formulários PENDING,
    ordena por priority DESC e created_at ASC (regra de negócio: emergências
    primeiro, dentro de cada nível atende os mais antigos), pega os primeiros
    `n` e aplica nearest-neighbor seedado em `start`.

    Não persiste nada. Recomputável on-demand.
    """

    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(
        self,
        requester_user_id: str,
        start_latitude: float,
        start_longitude: float,
        n: int,
        end_latitude: Optional[float] = None,
        end_longitude: Optional[float] = None,
    ) -> Tuple[List[Form], float]:
        candidates = self._fetch_pending_forms(requester_user_id)
        ordered_candidates = self._order_by_priority(candidates)
        top_n = ordered_candidates[:n]

        if not top_n:
            return [], 0.0

        points = [(form.latitude, form.longitude) for form in top_n]
        ordered_indices = order_by_nearest_neighbor(points, start=(start_latitude, start_longitude))
        ordered_forms = [top_n[i] for i in ordered_indices]

        end = (end_latitude, end_longitude) if end_latitude is not None and end_longitude is not None else None
        total_km = total_route_distance_km(
            ordered_points=[(form.latitude, form.longitude) for form in ordered_forms],
            start=(start_latitude, start_longitude),
            end=end,
        )

        return ordered_forms, total_km

    def _fetch_pending_forms(self, requester_user_id: str) -> List[Form]:
        # Pode haver mais PENDING do que cabe num único page do DynamoDB.
        # Pagina manualmente até esgotar — para um único user, o volume é
        # pequeno (dezenas no pior caso), então não vale a pena ler em chunks.
        all_forms: List[Form] = []
        exclusive_start_key: Optional[str] = None
        while True:
            page, next_key = self.form_repo.get_all_forms(
                limit=None,
                exclusive_start_key=exclusive_start_key,
                status=FormStatus.PENDING,
                user_id=requester_user_id,
            )
            all_forms.extend(page)
            if not next_key:
                break
            exclusive_start_key = next_key
        return all_forms

    @staticmethod
    def _order_by_priority(forms: List[Form]) -> List[Form]:
        # priority é enum cujo .value é string ('0', '1', '2', '3').
        # Convertemos para int para que 3 > 2 > 1 > 0 numerically.
        # Tie-breaker por created_at ASC (mais antigo primeiro).
        return sorted(
            forms,
            key=lambda f: (-int(f.priority.value), f.created_at),
        )
