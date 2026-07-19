import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_viewmodel import TemplateViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.helpers.viewmodels.form_dict_builders import build_field_vars_dict, build_section_dict


class TestCreateTemplateViewmodel:
    def _make_template(self):
        template_id = "d61dbf66-a10f-11ed-a8fc-0242ac120099"
        field = TextField(label="Name", required=True, key="name", order=0)
        section = Section(section_id=1, fields=[field])
        return Template(
            id=template_id,
            name="Template X",
            system="GAIA",
            description="Description",
            is_active=True,
            created_by="user-123",
            created_at=123,
            updated_at=123,
            sections=[section],
        )

    def test_field_vars_dict(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        result = build_field_vars_dict(field)
        assert result["field_type"] == "TEXT_FIELD"
        assert result["label"] == "Name"
        assert result["required"] is True

    def test_section_dict_with_vars_serializer(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        section = Section(section_id=1, fields=[field])
        result = build_section_dict(section, field_serializer=build_field_vars_dict)
        assert result["section_id"] == 1
        assert len(result["fields"]) == 1

    def test_template_viewmodel(self):
        template = self._make_template()
        vm = TemplateViewmodel(template)
        result = vm.to_dict()
        assert result["id"] == "d61dbf66-a10f-11ed-a8fc-0242ac120099"
        assert result["name"] == "Template X"
        assert result["is_active"] is True
        assert len(result["sections"]) == 1
