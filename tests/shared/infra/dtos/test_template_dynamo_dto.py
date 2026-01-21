import os
import sys

sys.path.append(os.getcwd())

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO


def _make_template(description="desc"):
    section = Section(
        section_id=1,
        fields=[TextField(label="Label", required=True, key="key", order=1)]
    )
    return Template(
        id="12345678-1234-1234-1234-123456789012",
        name="Template",
        description=description,
        system="GAIA",
        is_active=True,
        created_by="user-1",
        created_at=1,
        updated_at=2,
        sections=[section],
    )


def test_template_dynamo_dto_roundtrip():
    template = _make_template()
    dto = TemplateDynamoDTO.from_entity(template)
    data = dto.to_dynamo()

    assert data["template_id"] == template.id
    assert data["name"] == template.name
    assert data["description"] == template.description
    assert data["system"] == template.system
    assert data["is_active"] is True
    assert data["created_by"] == template.created_by
    assert data["created_at"] == template.created_at
    assert data["updated_at"] == template.updated_at
    assert data["sections"][0]["section_id"] == "1"

    roundtrip = TemplateDynamoDTO.from_dynamo(data).to_entity()
    assert roundtrip.id == template.id
    assert roundtrip.name == template.name
    assert roundtrip.description == template.description
    assert roundtrip.system == template.system
    assert roundtrip.is_active is True


def test_template_dynamo_dto_description_optional():
    template = _make_template(description=None)
    data = TemplateDynamoDTO.from_entity(template).to_dynamo()
    assert data["description"] is None
    roundtrip = TemplateDynamoDTO.from_dynamo(data).to_entity()
    assert roundtrip.description is None
