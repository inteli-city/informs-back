from typing import List, Optional, Tuple

from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllTemplatesUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(
        self,
        requester: UserGatewayDTO,
        systems: Optional[List[str]],
        limit: Optional[int],
        exclusive_start_key: Optional[str] = None,
        name_contains: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> Tuple[List[Template], Optional[str]]:
        if systems is not None and len(systems) == 0:
            raise EntityError("system")

        systems_to_use = systems if systems is not None else requester.systems
        if not systems_to_use:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        for system_name in systems_to_use:
            if system_name not in requester.systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        templates: List[Template] = []
        next_key = None

        if len(systems_to_use) == 1:
            start_key = None
            if exclusive_start_key is not None:
                start_key = try_decode_pagination_token(exclusive_start_key)
                if start_key is None:
                    raise InvalidPaginationToken()

            templates, next_key = self.template_repo.get_all_templates(
                system=systems_to_use[0],
                limit=limit,
                exclusive_start_key=start_key,
                name_contains=name_contains,
                is_active=is_active,
            )
        else:
            for system_name in systems_to_use:
                batch, _ = self.template_repo.get_all_templates(
                    system=system_name,
                    limit=None,
                    exclusive_start_key=None,
                    name_contains=name_contains,
                    is_active=is_active,
                )
                templates.extend(batch)

        templates = sorted(templates, key=lambda tpl: tpl.name.lower())

        if len(systems_to_use) > 1 and limit is not None:
            templates = templates[:limit]
            next_key = None

        return templates, next_key
