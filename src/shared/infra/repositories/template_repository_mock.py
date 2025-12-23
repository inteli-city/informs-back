from typing import List, Optional
from datetime import datetime, timezone
import uuid

from src.shared.domain.entities.section import Section
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository


class TemplateRepositoryMock(ITemplateRepository):
    templates: List[Template] = [
        Template(
            id="166e777a-d586-44b4-b90a-73618dfdc917",
            name="Default Template",
            description="Sample template",
            system="GAIA",
            is_active=True,
            created_by="user-1",
            created_at=int(datetime.now(timezone.utc).timestamp() * 1000),
            updated_at=int(datetime.now(timezone.utc).timestamp() * 1000),
            sections=[
                Section(
                    section_id=1,
                    fields=[
                        TextField(label="Name", required=True, key="name", order=1)
                    ]
                )
            ],
        )
    ]

    def __init__(self):
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        sample_field = TextField(label="Name", required=True, key="name", order=1)
        sample_section = Section(section_id=1, fields=[sample_field])
        base_template = Template(
            id=str(uuid.uuid4()),
            name="Default Template",
            description="Sample template",
            system="GAIA",
            is_active=True,
            created_by="user-1",
            created_at=now,
            updated_at=now,
            sections=[sample_section],
        )
        self.templates = [base_template]

    def create_template(self, template: Template) -> Template:
        self.templates.append(template)
        return template

    def get_template(self, template_id: str) -> Optional[Template]:
        for tpl in self.templates:
            if tpl.id == template_id:
                return tpl
        return None

    def get_all_templates(self) -> List[Template]:
        return list(self.templates)

    def update_template(self, template: Template) -> Template:
        for idx, tpl in enumerate(self.templates):
            if tpl.id == template.id:
                self.templates[idx] = template
                return template
        raise ValueError("Template not found")
