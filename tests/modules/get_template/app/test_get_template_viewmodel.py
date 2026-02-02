import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.modules.get_template.app.get_template_viewmodel import GetTemplateViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template


class TestGetTemplateViewmodel:
    def _make_template(self):
        template_id = str(uuid.uuid4())
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
            updated_at=456,
            sections=[section],
        )

    def test_get_template_viewmodel(self):
        template = self._make_template()
        viewmodel = GetTemplateViewmodel(template)

        result = viewmodel.to_dict()

        assert result["id"] == template.id
        assert result["name"] == "Template X"
        assert result["is_active"] is True
        assert len(result["sections"]) == 1
        assert result["created_at"] == 123
        assert result["updated_at"] == 456
