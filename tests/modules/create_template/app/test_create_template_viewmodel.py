import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_viewmodel import FieldViewmodel, SectionViewmodel, TemplateViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template


class TestCreateTemplateViewmodel:
    def _make_template(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        section = Section(section_id=1, fields=[field])
        return Template(
            id="template-id",
            name="Template X",
            system="GAIA",
            description="Description",
            is_active=True,
            created_by="user-123",
            created_at=123,
            updated_at=123,
            sections=[section],
        )

    def test_field_viewmodel(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        vm = FieldViewmodel(field)
        result = vm.to_dict()
        assert result["field_type"] == "TEXT_FIELD"
        assert result["label"] == "Name"
        assert result["required"] is True

    def test_section_viewmodel(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        section = Section(section_id=1, fields=[field])
        vm = SectionViewmodel(section)
        result = vm.to_dict()
        assert result["section_id"] == 1
        assert len(result["fields"]) == 1

    def test_template_viewmodel(self):
        template = self._make_template()
        vm = TemplateViewmodel(template)
        result = vm.to_dict()
        assert result["id"] == "template-id"
        assert result["name"] == "Template X"
        assert result["isActive"] is True
        assert len(result["sessions"]) == 1
