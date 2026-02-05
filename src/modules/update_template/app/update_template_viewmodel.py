from enum import Enum
from typing import List

from src.shared.domain.entities.field import Field
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template


class FieldViewmodel:
    def __init__(self, field: Field):
        self.field = field

    def to_dict(self):
        return {
            attr: getattr(self.field, attr).value if isinstance(getattr(self.field, attr), Enum) else getattr(self.field, attr)
            for attr in vars(self.field)
        }


class SectionViewmodel:
    def __init__(self, section: Section):
        self.section = section

    def to_dict(self):
        return {
            "section_id": self.section.section_id,
            "fields": [FieldViewmodel(field).to_dict() for field in self.section.fields],
        }


class TemplateViewmodel:
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
