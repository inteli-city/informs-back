from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(self, template_id: str, requester: UserGatewayDTO) -> Template:
        template = self.template_repo.get_template(template_id)

        if template is None or not template.is_active:
            raise NoItemsFound("Template não encontrado")

        if template.system not in requester.systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este template")

        return template
