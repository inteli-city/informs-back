from typing import List, Optional, Tuple, Union

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllFormsUsecase:
    def __init__(self, form_repo: IFormRepository, access_control: Optional[AccessControl] = None):
        self.form_repo = form_repo
        self.access_control = access_control

    def __call__(
        self,
        requester: UserGatewayDTO,
        limit: Optional[int],
        exclusive_start_key: Optional[str] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
        system: Optional[List[str]] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
        scope: str = "mine",
    ) -> Tuple[List[Form], Optional[str]]:
        if system is not None and len(system) == 0:
            raise EntityError("Lista de sistemas não pode ser vazia")

        systems_to_use = system if system is not None else requester.systems
        if not systems_to_use:
            raise ForbiddenAction("Usuário não tem permissão para acessar sistemas")

        for system_name in systems_to_use:
            if system_name not in requester.systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        start_key = None
        if exclusive_start_key is not None:
            start_key = try_decode_pagination_token(exclusive_start_key)
            if start_key is None:
                raise InvalidPaginationToken()

        # scope=pool (especificação Uberlândia §6.3): OS abertas via GSI3, sem
        # cair em Scan (§14.1) — a filtragem fina por escopo é a Fase 2.
        if scope == "pool":
            if len(systems_to_use) != 1:
                raise EntityError("scope=pool exige um único system")
            return self.form_repo.get_pool_forms(system=systems_to_use[0], limit=limit, exclusive_start_key=start_key)

        # scope=all (RN-UBE-003, decisão P3): quem tem `forms.view_all` em
        # todos os sistemas pedidos enxerga todo mundo, não só o próprio.
        # Mesmo caminho de get_all_forms de sempre (user_id=None), só com o
        # gate de permissão na frente.
        if scope == "all":
            self._ensure_requester_can_see_all(requester.user_id, systems_to_use)
            return self.form_repo.get_all_forms(
                limit=limit, exclusive_start_key=start_key, status=status, system=systems_to_use,
                user_id=None, created_at_start=created_at_start, created_at_end=created_at_end, search=search,
            )

        return self.form_repo.get_all_forms(
            limit=limit,
            exclusive_start_key=start_key,
            status=status,
            system=systems_to_use,
            user_id=requester.user_id,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
            search=search,
        )

    def _ensure_requester_can_see_all(self, requester_user_id: str, systems: List[str]) -> None:
        if self.access_control is None or not all(
            self.access_control.can(requester_user_id, system, Action.FORMS_VIEW_ALL) for system in systems
        ):
            raise ForbiddenAction("Usuário não pode ver todas as OS destes sistemas")
