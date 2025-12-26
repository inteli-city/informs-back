from typing import List, Optional, Tuple

from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetAllTemplatesUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(
        self,
        requester: UserGatewayDTO,
        system: str,
        limit: int,
        exclusive_start_key: Optional[str] = None,
        name_contains: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> Tuple[List[Template], Optional[str]]:
        if system not in requester.systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        templates, next_key = self.template_repo.get_all_templates(
            system=system,
            limit=limit,
            exclusive_start_key=exclusive_start_key,
            name_contains=name_contains,
            is_active=is_active,
        )

        templates = sorted(templates, key=lambda tpl: tpl.name.lower())

        return templates, next_key
