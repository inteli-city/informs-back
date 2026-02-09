from typing import List, Optional, Tuple, Union

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllFormsUsecase:
    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(
        self,
        requester: UserGatewayDTO,
        limit: Optional[int],
        exclusive_start_key: Optional[str] = None,
        status: Optional[Union[FORM_STATUS, List[FORM_STATUS]]] = None,
        system: Optional[List[str]] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        if system is not None and len(system) == 0:
            raise EntityError("system")

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
