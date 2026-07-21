from src.shared.domain.entities.template import Template
from src.shared.helpers.contracts.endpoints.create_template_contract import CreateTemplateResponseSchema
from src.shared.helpers.viewmodels.form_dict_builders import build_field_vars_dict, build_section_dict


class TemplateViewmodel:
    template: Template

    def __init__(self, template: Template):
        self.template = template

    def to_dict(self):
        payload = {
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
        return CreateTemplateResponseSchema.model_validate(payload).model_dump()
