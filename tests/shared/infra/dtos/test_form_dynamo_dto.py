"""
Antes deste refactor, os 4 testes (from_entity, to_dynamo, from_dynamo,
to_entity) repetiam ~50 linhas de setup e ~30 linhas de asserts cada,
totalizando ~208 linhas duplicadas detectadas pelo SonarCloud.

Agora cada teste tem só o setup específico do seu caso e usa helpers
compartilhados para asserts comuns.
"""

import pytest

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO


# Constantes de teste — usadas por todos os 4 cenários.
SAMPLE_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120010"
SAMPLE_TS = 12345678
SAMPLE_FIELD = TextField(
    placeholder="placeholder", required=True, key="key", regex="regex",
    formatting="formatting", max_length=10, value="poggers",
)


def _build_justification() -> Justification:
    return Justification(
        options=[
            JustificationOption(option="option", required_image=True, required_text=True),
        ],
        selected_option="option",
        justification_text="justification_text",
        justification_image="justification_image",
    )


def _common_kwargs() -> dict:
    """Kwargs compartilhados entre Form e FormDynamoDTO — assinaturas iguais."""
    return {
        "form_title": "form_title",
        "id": SAMPLE_ID,
        "created_by": SAMPLE_ID,
        "user_id": SAMPLE_ID,
        "template": "template",
        "area": "area",
        "system": "system",
        "street": "street",
        "city": "city",
        "number": 123,
        "latitude": 0.0,
        "longitude": 0.0,
        "observation": "observation",
        "priority": Priority.EMERGENCY,
        "status": FormStatus.IN_PROGRESS,
        "expiration_date": SAMPLE_TS,
        "created_at": SAMPLE_TS,
        "updated_at": SAMPLE_TS,
        "in_progress_at": SAMPLE_TS,
        "completed_at": SAMPLE_TS,
        "justification": _build_justification(),
        "sections": [Section(section_id=0, fields=[SAMPLE_FIELD])],
        "information_fields": [TextInformationField(value="value")],
    }


def _build_form() -> Form:
    return Form(**_common_kwargs())


def _build_form_dto() -> FormDynamoDTO:
    return FormDynamoDTO(**_common_kwargs())


def _dynamo_dict() -> dict:
    return {
        "form_title": "form_title",
        "created_by": SAMPLE_ID,
        "user_id": SAMPLE_ID,
        "PK": f"form#{SAMPLE_ID}",
        "SK": "METADATA",
        "template": "template",
        "area": "area",
        "system": "system",
        "street": "street",
        "city": "city",
        "number": 123,
        "latitude": 0.0,
        "longitude": 0.0,
        "observation": "observation",
        "priority": Priority.EMERGENCY.value,
        "status": FormStatus.IN_PROGRESS.value,
        "expiration_date": SAMPLE_TS,
        "created_at": SAMPLE_TS,
        "updated_at": SAMPLE_TS,
        "in_progress_at": SAMPLE_TS,
        "completed_at": SAMPLE_TS,
        "justification": {
            "options": [
                {"option": "option", "required_image": True, "required_text": True},
            ],
            "selected_option": "option",
            "justification_text": "justification_text",
            "justification_image": "justification_image",
        },
        "sections": [
            {
                "section_id": "0",
                "fields": [
                    {
                        "field_type": "TEXT_FIELD",
                        "placeholder": "placeholder",
                        "required": True,
                        "key": "key",
                        "regex": "regex",
                        "formatting": "formatting",
                        "max_length": 10,
                        "value": "poggers",
                    },
                ],
            },
        ],
        "information_fields": [
            {"information_field_type": "TEXT_INFORMATION_FIELD", "value": "value"},
        ],
    }


def _assert_object_attrs(obj):
    """Asserts comuns para Form, FormDynamoDTO e o entity recuperado por to_entity."""
    assert obj.form_title == "form_title"
    assert obj.id == SAMPLE_ID
    assert obj.created_by == SAMPLE_ID
    assert obj.user_id == SAMPLE_ID
    assert obj.template == "template"
    assert obj.area == "area"
    assert obj.system == "system"
    assert obj.street == "street"
    assert obj.city == "city"
    assert obj.number == 123
    assert obj.latitude == pytest.approx(0.0, abs=1e-9)
    assert obj.longitude == pytest.approx(0.0, abs=1e-9)
    assert obj.observation == "observation"
    assert obj.priority == Priority.EMERGENCY
    assert obj.status == FormStatus.IN_PROGRESS
    assert obj.expiration_date == SAMPLE_TS
    assert obj.created_at == SAMPLE_TS
    assert obj.in_progress_at == SAMPLE_TS
    assert obj.completed_at == SAMPLE_TS
    assert obj.justification.options[0].option == "option"
    assert obj.justification.options[0].required_image is True
    assert obj.justification.options[0].required_text is True
    assert obj.justification.selected_option == "option"
    assert obj.justification.justification_text == "justification_text"
    assert obj.justification.justification_image == "justification_image"
    assert obj.sections[0].section_id == 0
    assert obj.sections[0].fields[0].placeholder == "placeholder"
    assert obj.sections[0].fields[0].required is True
    assert obj.sections[0].fields[0].key == "key"
    assert obj.sections[0].fields[0].regex == "regex"
    assert obj.sections[0].fields[0].formatting == "formatting"
    assert obj.sections[0].fields[0].max_length == 10
    assert obj.sections[0].fields[0].value == "poggers"
    assert obj.information_fields[0].value == "value"


def _assert_dynamo_dict(form_dict: dict):
    """Asserts específicos do dict que vai pro DynamoDB (chaves string)."""
    assert form_dict["form_title"] == "form_title"
    assert form_dict["created_by"] == SAMPLE_ID
    assert form_dict["user_id"] == SAMPLE_ID
    assert form_dict["template"] == "template"
    assert form_dict["area"] == "area"
    assert form_dict["system"] == "system"
    assert form_dict["street"] == "street"
    assert form_dict["city"] == "city"
    assert form_dict["number"] == 123
    assert form_dict["latitude"] == pytest.approx(0.0, abs=1e-9)
    assert form_dict["longitude"] == pytest.approx(0.0, abs=1e-9)
    assert form_dict["priority"] == Priority.EMERGENCY.value
    assert form_dict["status"] == FormStatus.IN_PROGRESS.value
    assert form_dict["expiration_date"] == SAMPLE_TS
    assert form_dict["created_at"] == SAMPLE_TS
    assert form_dict["updated_at"] == SAMPLE_TS
    assert form_dict["in_progress_at"] == SAMPLE_TS
    assert form_dict["completed_at"] == SAMPLE_TS
    assert form_dict["justification"]["options"][0]["option"] == "option"
    assert form_dict["justification"]["options"][0]["required_image"] is True
    assert form_dict["justification"]["options"][0]["required_text"] is True
    assert form_dict["justification"]["selected_option"] == "option"
    assert form_dict["justification"]["justification_text"] == "justification_text"
    assert form_dict["justification"]["justification_image"] == "justification_image"
    assert form_dict["sections"][0]["section_id"] == "0"
    assert form_dict["sections"][0]["fields"][0]["placeholder"] == "placeholder"
    assert form_dict["sections"][0]["fields"][0]["required"] is True
    assert form_dict["sections"][0]["fields"][0]["key"] == "key"
    assert form_dict["sections"][0]["fields"][0]["regex"] == "regex"
    assert form_dict["sections"][0]["fields"][0]["formatting"] == "formatting"
    assert form_dict["sections"][0]["fields"][0]["max_length"] == 10
    assert form_dict["sections"][0]["fields"][0]["value"] == "poggers"
    assert form_dict["information_fields"][0]["value"] == "value"


class TestFormDynamoDTO:
    def test_from_entity(self):
        form_dto = FormDynamoDTO.from_entity(_build_form())
        _assert_object_attrs(form_dto)

    def test_to_dynamo(self):
        form_dict = _build_form_dto().to_dynamo()
        _assert_dynamo_dict(form_dict)

    def test_from_dynamo(self):
        form = FormDynamoDTO.from_dynamo(_dynamo_dict())
        _assert_object_attrs(form)

    def test_to_entity(self):
        form = _build_form_dto().to_entity()
        _assert_object_attrs(form)
        assert form.updated_at == SAMPLE_TS  # to_entity-specific extra check
