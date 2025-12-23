from typing import List, Optional

from src.modules.create_template.app.create_template_viewmodel import TemplateViewmodel
from src.shared.domain.entities.template import Template


class GetAllTemplatesViewmodel:
    def __init__(self, templates: List[Template], limit: int, last_evaluated_key: Optional[dict], system: str):
        self.templates = templates
        self.limit = limit
        self.last_evaluated_key = last_evaluated_key
        self.system = system

    def to_dict(self):
        return {
            "templates": [TemplateViewmodel(template).to_dict() for template in self.templates],
            "limit": self.limit,
            "system": self.system,
            "last_evaluated_key": self.last_evaluated_key,
        }
