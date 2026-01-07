import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.modules.get_all_templates.app.get_all_templates_viewmodel import GetAllTemplatesViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.helpers.functions.pagination_token import decode_pagination_token, encode_pagination_token


class TestGetAllTemplatesViewmodel:
    def _make_template(self, name: str):
        field = TextField(label="Name", required=True, key="name", order=0)
        section = Section(section_id=1, fields=[field])
        return Template(
            id=str(uuid.uuid4()),
            name=name,
            system="GAIA",
            description=None,
            is_active=True,
            created_by="user-123",
            created_at=111,
            updated_at=222,
            sections=[section],
        )

    def test_get_all_templates_viewmodel(self):
        templates = [self._make_template("Template 1"), self._make_template("Template 2")]

        token = encode_pagination_token({"PK": "template#1"})
        viewmodel = GetAllTemplatesViewmodel(templates=templates, limit=20, last_evaluated_key=token, system="GAIA")
        result = viewmodel.to_dict()

        assert result["limit"] == 20
        assert result["system"] == "GAIA"
        decoded = decode_pagination_token(result["last_evaluated_key"])
        assert decoded["PK"] == "template#1"
        assert len(result["templates"]) == 2
        assert result["templates"][0]["is_active"] is True
