from typing import List, Optional, Tuple

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import FormsNotFound
from src.shared.helpers.functions.nearest_neighbor import (
    order_by_nearest_neighbor,
    total_route_distance_km,
)


class PlanRouteUsecase:
    """
    Stateless route planner com dois modos mutuamente exclusivos:

    - Modo `n`: o backend escolhe os primeiros N PENDING do requester,
      ordenados por priority DESC e created_at ASC (emergências primeiro,
      dentro de cada nível atende os mais antigos).
    - Modo `form_ids`: o cliente passa explicitamente os IDs e o backend
      apenas valida que pertencem ao requester (independente de status) e
      ordena via nearest-neighbor.

    Em ambos os casos aplica nearest-neighbor seedado em `start` e calcula
    a distância total da rota (Haversine), incluindo o segmento até `end`
    se este for fornecido. Não persiste nada — recomputável on-demand.
    """

    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(
        self,
        requester_user_id: str,
        start_latitude: float,
        start_longitude: float,
        n: Optional[int] = None,
        form_ids: Optional[List[str]] = None,
        end_latitude: Optional[float] = None,
        end_longitude: Optional[float] = None,
    ) -> Tuple[List[Form], float]:
        if form_ids is not None:
            forms_to_order = self._fetch_forms_by_ids(requester_user_id, form_ids)
        else:
            candidates = self._fetch_pending_forms(requester_user_id)
            ordered_candidates = self._order_by_priority(candidates)
            forms_to_order = ordered_candidates[: n or 0]

        if not forms_to_order:
            return [], 0.0

        points = [(form.latitude, form.longitude) for form in forms_to_order]
        ordered_indices = order_by_nearest_neighbor(points, start=(start_latitude, start_longitude))
        ordered_forms = [forms_to_order[i] for i in ordered_indices]

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
                status=FORM_STATUS.PENDING,
                user_id=requester_user_id,
            )
            all_forms.extend(page)
            if not next_key:
                break
            exclusive_start_key = next_key
        return all_forms

    def _fetch_forms_by_ids(self, requester_user_id: str, form_ids: List[str]) -> List[Form]:
        # Por enquanto (v1) a regra é simples: form_id precisa pertencer ao
        # requester. Quando a tabela de Profile entrar, gestores vão poder
        # passar IDs de outros motoverificadores — a regra muda aqui.
        # Faz GetItem 1-a-1; o repo já cacheia idempotente. Para até 50 IDs,
        # latência total é desprezível em DynamoDB.
        found: List[Form] = []
        missing: List[str] = []
        for form_id in form_ids:
            form = self.form_repo.get_form_by_id(user_id=requester_user_id, form_id=form_id)
            if form is None or form.user_id != requester_user_id:
                missing.append(form_id)
                continue
            found.append(form)

        if missing:
            raise FormsNotFound(missing_form_ids=missing)

        return found

    @staticmethod
    def _order_by_priority(forms: List[Form]) -> List[Form]:
        # priority é enum cujo .value é string ('0', '1', '2', '3').
        # Convertemos para int para que 3 > 2 > 1 > 0 numerically.
        # Tie-breaker por created_at ASC (mais antigo primeiro).
        return sorted(
            forms,
            key=lambda f: (-int(f.priority.value), f.created_at),
        )
