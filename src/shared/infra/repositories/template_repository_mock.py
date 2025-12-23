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

    def _parse_start_index(self, templates: List[Template], last_evaluated_key: Optional[dict]) -> int:
        if last_evaluated_key is None:
            return 0

        last_id = last_evaluated_key.get("id") or last_evaluated_key.get("template_id")

        pk = last_evaluated_key.get("PK") or last_evaluated_key.get("pk")
        if last_id is None and pk and isinstance(pk, str) and pk.startswith("template#"):
            last_id = pk.split("template#", 1)[1]

        if last_id is None:
            return 0

        for idx, tpl in enumerate(templates):
            if tpl.id == last_id:
                return idx + 1
        return 0

    def get_all_templates(
        self,
        system: str,
        limit: int,
        last_evaluated_key: Optional[dict] = None,
        name_contains: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> tuple[List[Template], Optional[dict]]:
        filtered = [tpl for tpl in self.templates if tpl.system == system]

        if is_active is not None:
            filtered = [tpl for tpl in filtered if tpl.is_active == is_active]

        if name_contains is not None:
            name_lower = str(name_contains).lower()
            filtered = [tpl for tpl in filtered if name_lower in tpl.name.lower()]

        filtered.sort(key=lambda tpl: tpl.name.lower())

        start = self._parse_start_index(filtered, last_evaluated_key)
        end = start + limit
        page = filtered[start:end]

        next_key = None
        if end < len(filtered):
            next_tpl = filtered[end - 1]
            next_key = {
                "PK": f"template#{next_tpl.id}",
                "SK": "METADATA",
                "GSI1PK": f"system#{next_tpl.system}",
                "GSI1SK": f"active#{int(next_tpl.is_active)}#name#{next_tpl.name}#template#{next_tpl.id}",
            }

        return page, next_key

    def update_template(self, template: Template) -> Template:
        for idx, tpl in enumerate(self.templates):
            if tpl.id == template.id:
                self.templates[idx] = template
                return template
        raise ValueError("Template not found")
