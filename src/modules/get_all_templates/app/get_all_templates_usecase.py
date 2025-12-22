from typing import List, Optional

from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository


class GetAllTemplatesUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(
        self,
        page: int,
        limit: int,
        is_active: Optional[bool] = None,
        system: Optional[str] = None,
    ) -> List[Template]:
        templates = self.template_repo.get_all_templates()

        if is_active is not None:
            templates = [template for template in templates if template.is_active == is_active]

        if system is not None:
            templates = [template for template in templates if template.system == system]

        templates = sorted(templates, key=lambda tpl: tpl.updated_at or 0, reverse=True)

        start = (page - 1) * limit
        end = start + limit
        return templates[start:end]
