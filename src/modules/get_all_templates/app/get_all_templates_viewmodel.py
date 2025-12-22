from typing import List

from src.modules.create_template.app.create_template_viewmodel import TemplateViewmodel
from src.shared.domain.entities.template import Template


class GetAllTemplatesViewmodel:
    def __init__(self, templates: List[Template], page: int, limit: int):
        self.templates = templates
        self.page = page
        self.limit = limit

    def to_dict(self):
        return {
            "templates": [TemplateViewmodel(template).to_dict() for template in self.templates],
            "page": self.page,
            "limit": self.limit,
        }
