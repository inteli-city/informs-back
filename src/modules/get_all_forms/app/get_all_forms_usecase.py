import time
from dataclasses import dataclass
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

# Limite padrão do pool: sem `limit`, a Lambda GetAllForms estoura o timeout de
# 15 s no DEV com ~2 mil OS (limit=1000 já levou 7,9 s). O app ainda chama sem
# paginação; enquanto o front não pagina, o back aplica 200 — página que cabe
# com folga na janela da Lambda e volta comprimida pelo API Gateway.
POOL_DEFAULT_LIMIT = 200


@dataclass(frozen=True)
class GetAllFormsDelta:
    """Resposta da consulta incremental: `in_pool[i]` diz se `forms[i]` ainda está no pool (False vira marcador)."""

    forms: List[Form]
    in_pool: List[bool]
    next_key: Optional[str]
    server_time: int


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
        systems_to_use = self._systems_to_use(requester, system)
        start_key = self._decode_start_key(exclusive_start_key)

        # scope=pool (especificação Uberlândia §6.3): OS abertas via GSI3, sem
        # cair em Scan (§14.1). Só as sem grupo e as dos grupos de quem pede
        # (ADR-0022).
        if scope == "pool":
            if len(systems_to_use) != 1:
                raise EntityError("scope=pool exige um único system")
            effective_limit = limit if limit is not None else POOL_DEFAULT_LIMIT
            groups = (
                self.access_control.groups_in(requester.user_id, systems_to_use[0])
                if self.access_control is not None else None
            )
            return self.form_repo.get_pool_forms(
                system=systems_to_use[0], limit=effective_limit, exclusive_start_key=start_key, groups=groups,
            )

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

    def get_changes(
        self,
        requester: UserGatewayDTO,
        limit: Optional[int],
        exclusive_start_key: Optional[str],
        system: Optional[List[str]],
        updated_after: int,
        scope: str,
    ) -> GetAllFormsDelta:
        """Consulta incremental (`updated_after`): só o que mudou depois do instante, em ordem crescente.

        O `server_time` é lido antes de qualquer consulta: o cliente o usa como próximo `updated_after`, e uma OS
        gravada durante a consulta cai no próximo ciclo em vez de se perder.
        """
        server_time = int(time.time() * 1000)
        systems_to_use = self._systems_to_use(requester, system)
        start_key = self._decode_start_key(exclusive_start_key)

        if scope == "pool":
            if len(systems_to_use) != 1:
                raise EntityError("scope=pool exige um único system")
            effective_limit = limit if limit is not None else POOL_DEFAULT_LIMIT
            pairs, next_key = self.form_repo.get_pool_changes(
                system=systems_to_use[0],
                updated_after=updated_after,
                limit=effective_limit,
                exclusive_start_key=start_key,
            )
            return GetAllFormsDelta(
                forms=[form for form, _ in pairs],
                in_pool=[in_pool for _, in_pool in pairs],
                next_key=next_key,
                server_time=server_time,
            )

        # scope=mine: o índice por usuário não tem a ordem de `updated_at`, então a página sai ordenada por
        # ele dentro dela. Entre páginas, a ordem é a do índice (o cursor do Dynamo não aceita outra).
        forms, next_key = self.form_repo.get_all_forms(
            limit=limit,
            exclusive_start_key=start_key,
            system=systems_to_use,
            user_id=requester.user_id,
            updated_at_start=updated_after + 1,
        )
        forms = sorted(forms, key=lambda form: (form.updated_at, form.id))
        return GetAllFormsDelta(
            forms=forms,
            in_pool=[True] * len(forms),
            next_key=next_key,
            server_time=server_time,
        )

    @staticmethod
    def _systems_to_use(requester: UserGatewayDTO, system: Optional[List[str]]) -> List[str]:
        if system is not None and len(system) == 0:
            raise EntityError("Lista de sistemas não pode ser vazia")

        systems_to_use = system if system is not None else requester.systems
        if not systems_to_use:
            raise ForbiddenAction("Usuário não tem permissão para acessar sistemas")

        for system_name in systems_to_use:
            if system_name not in requester.systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")
        return systems_to_use

    @staticmethod
    def _decode_start_key(exclusive_start_key: Optional[str]) -> Optional[dict]:
        if exclusive_start_key is None:
            return None
        start_key = try_decode_pagination_token(exclusive_start_key)
        if start_key is None:
            raise InvalidPaginationToken()
        return start_key

    def _ensure_requester_can_see_all(self, requester_user_id: str, systems: List[str]) -> None:
        if self.access_control is None or not all(
            self.access_control.can(requester_user_id, system, Action.FORMS_VIEW_ALL) for system in systems
        ):
            raise ForbiddenAction("Usuário não pode ver todas as OS destes sistemas")
