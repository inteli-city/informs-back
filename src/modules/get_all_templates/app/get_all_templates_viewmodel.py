from typing import List, Optional

from src.shared.domain.entities.template import Template
from src.shared.helpers.contracts.endpoints.get_all_templates_contract import GetAllTemplatesResponseSchema
from src.shared.helpers.viewmodels.form_dict_builders import build_field_vars_dict, build_section_dict


class TemplateViewmodel:
    template: Template

    def __init__(self, template: Template):
        self.template = template

    def to_dict(self):
        return {
            "id": self.template.id,
            "name": self.template.name,
            "system": self.template.system,
            "description": self.template.description,
            "is_active": self.template.is_active,
            "sections": [
                build_section_dict(section, field_serializer=build_field_vars_dict)
                for section in self.template.sections
            ],
            "created_by": self.template.created_by,
            "created_at": self.template.created_at,
            "updated_at": self.template.updated_at,
        }


class GetAllTemplatesViewmodel:
    def __init__(self, templates: List[Template], limit: Optional[int], last_evaluated_key: Optional[str], systems: List[str]):
        self.templates = templates
        self.limit = limit
        self.last_evaluated_key = last_evaluated_key
        self.systems = systems

    def to_dict(self):
        payload = {
            "templates": [TemplateViewmodel(template).to_dict() for template in self.templates],
            "limit": self.limit,
            "last_evaluated_key": self.last_evaluated_key,
        }
        if self.systems is not None:
            payload["systems"] = self.systems
        validated = GetAllTemplatesResponseSchema.model_validate(payload).model_dump()
        if self.systems is not None and len(self.systems) == 1:
            validated["system"] = self.systems[0]
        return validated
