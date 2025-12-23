import os
import sys
from datetime import datetime, timezone

sys.path.append(os.getcwd())

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


def make_template():
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    section = Section(section_id=1, fields=[TextField(label="Field", required=True, key="field", order=1)])
    return Template(
        name="Repo Template",
        system="GAIA",
        created_by="user-1",
        created_at=now,
        updated_at=now,
        sections=[section],
    )


class TestTemplateRepositoryMock:
    def test_create_and_get(self):
        repo = TemplateRepositoryMock()
        tpl = make_template()
        repo.create_template(tpl)

        fetched = repo.get_template(tpl.id)
        assert fetched.id == tpl.id
        templates, _ = repo.get_all_templates(system="GAIA", limit=10, is_active=None)
        assert len(templates) >= 2

    def test_update_template(self):
        repo = TemplateRepositoryMock()
        tpl = repo.templates[0]
        tpl.change_name("Updated")
        repo.update_template(tpl)

        fetched = repo.get_template(tpl.id)
        assert fetched.name == "Updated"
