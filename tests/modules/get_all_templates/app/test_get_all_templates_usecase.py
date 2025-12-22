import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.append(os.getcwd())

from src.modules.get_all_templates.app.get_all_templates_usecase import GetAllTemplatesUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


def _make_template(name: str, system: str, is_active: bool, updated_at: int) -> Template:
    section = Section(section_id=1, fields=[TextField(label="Field", required=True, key="field", order=1)])
    return Template(
        id=str(uuid.uuid4()),
        name=name,
        system=system,
        description=None,
        is_active=is_active,
        created_by="tester",
        created_at=updated_at,
        updated_at=updated_at,
        sections=[section],
    )


class TestGetAllTemplatesUsecase:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = GetAllTemplatesUsecase(self.repo)

        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.repo.templates.append(_make_template("Template A", "GAIA", True, now + 1000))
        self.repo.templates.append(_make_template("Template B", "ORION", False, now + 2000))

    def test_get_all_templates_usecase_filters_and_orders(self):
        templates = self.usecase(page=1, limit=20, is_active=True, system="GAIA")

        assert len(templates) >= 1
        assert all(template.is_active for template in templates)
        assert all(template.system == "GAIA" for template in templates)
        assert templates == sorted(templates, key=lambda tpl: tpl.updated_at, reverse=True)

    def test_get_all_templates_usecase_pagination(self):
        templates_page_1 = self.usecase(page=1, limit=20)
        templates_page_2 = self.usecase(page=2, limit=20)

        assert len(templates_page_1) >= 1
        assert len(templates_page_2) == 0
