from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.usecase_errors import NoItemsFound


class GetTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(self, template_id: str) -> Template:
        template = self.template_repo.get_template(template_id)

        if template is None:
            raise NoItemsFound("Template não encontrado")

        return template
