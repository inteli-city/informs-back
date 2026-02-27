from enum import Enum
from typing import List, Optional
from src.shared.domain.entities.field import Field
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.helpers.contracts.endpoints.get_all_templates_contract import GetAllTemplatesResponseSchema


class FieldViewmodel:
    field: Field

    def __init__(self, field: Field):
        self.field = field

    def to_dict(self):
        return {
            attr: getattr(self.field, attr).value if isinstance(getattr(self.field, attr), Enum) else getattr(self.field, attr)
            for attr in vars(self.field)
        }


class SectionViewmodel:
    section: Section

    def __init__(self, section: Section):
        self.section = section

    def to_dict(self):
        return {
            "section_id": self.section.section_id,
            "fields": [FieldViewmodel(field).to_dict() for field in self.section.fields],
        }


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
            "sections": [SectionViewmodel(section).to_dict() for section in self.template.sections],
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
