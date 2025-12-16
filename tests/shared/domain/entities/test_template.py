import os
import sys
from datetime import datetime, timezone

sys.path.append(os.getcwd())

import pytest

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.helpers.errors.domain_errors import EntityError


def make_template(now=None):
    now = now or int(datetime.now(timezone.utc).timestamp() * 1000)
    section = Section(section_id=1, fields=[TextField(label="Field", required=True, key="field", order=1)])
    return Template(
        name="Template A",
        system="GAIA",
        created_by="user-1",
        created_at=now,
        updated_at=now,
        sections=[section],
    )


class TestTemplateEntity:
    def test_create_template_success(self):
        tpl = make_template()
        assert tpl.name == "Template A"
        assert tpl.is_active is True
        assert tpl.sections[0].section_id == 1

    def test_invalid_name(self):
        with pytest.raises(EntityError):
            make_template().changeName("", int(datetime.now(timezone.utc).timestamp() * 1000))

    def test_change_description(self):
        tpl = make_template()
        new_time = tpl.updated_at + 1
        tpl.changeDescription("New desc", new_time)
        assert tpl.description == "New desc"
        assert tpl.updated_at == new_time

    def test_change_sections(self):
        tpl = make_template()
        new_time = tpl.updated_at + 2
        new_section = Section(section_id=2, fields=[TextField(label="Other", required=False, key="other", order=1)])
        tpl.changeSections([new_section], new_time)
        assert tpl.sections[0].section_id == 2
        assert tpl.updated_at == new_time

    def test_accepts_template_id_alias(self):
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        section = Section(section_id=1, fields=[TextField(label="Field", required=True, key="field", order=1)])
        tpl = Template(
            name="Template B",
            system="GAIA",
            created_by="user-1",
            created_at=now,
            updated_at=now,
            sections=[section],
            template_id="d61dbf66-a10f-11ed-a8fc-0242ac120099",
        )
        assert tpl.id == "d61dbf66-a10f-11ed-a8fc-0242ac120099"
        assert tpl.template_id == tpl.id
