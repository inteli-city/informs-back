import os
import sys

import pytest

sys.path.append(os.getcwd())

pydantic = pytest.importorskip("pydantic")
ValidationError = pydantic.ValidationError

from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.helpers.contracts.endpoints.create_form_contract import (
    CreateFormRequestSchema,
    CreateFormResponseSchema,
)
from src.shared.helpers.contracts.openapi_contract_generator import build_openapi_from_contracts
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


def _base_create_form_request():
    return {
        "form_title": "FORM TITLE",
        "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
        "system": "GAIA",
        "street": "1",
        "city": "1",
        "latitude": 1.0,
        "longitude": 1.0,
        "priority": 3,
        "justifications": [
            {"option": "option", "required_image": True, "required_text": True}
        ],
        "sections": [
            {
                "section_id": 1,
                "fields": [
                    {
                        "field_type": "TEXT_FIELD",
                        "label": "placeholder",
                        "required": True,
                        "key": "key",
                        "order": 0,
                        "regex": "regex",
                        "max_length": 10,
                    }
                ],
            }
        ],
        "information_fields": [
            {"information_field_type": "TEXT_INFORMATION_FIELD", "value": "value"}
        ],
        "observation": "obs",
    }


def test_create_form_request_contract_accepts_regular_payload():
    payload = _base_create_form_request()
    parsed = CreateFormRequestSchema.model_validate(payload)
    assert parsed.form_title == payload["form_title"]
    assert parsed.sections is not None
    assert len(parsed.sections) == 1


def test_create_form_request_contract_allows_missing_sections_with_uuid_template():
    payload = _base_create_form_request()
    payload["template"] = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
    payload.pop("sections")
    parsed = CreateFormRequestSchema.model_validate(payload)
    assert parsed.template is not None
    assert parsed.sections is None


def test_create_form_request_contract_rejects_missing_sections_without_uuid_template():
    payload = _base_create_form_request()
    payload["template"] = "not-a-uuid"
    payload.pop("sections")
    with pytest.raises(ValidationError):
        CreateFormRequestSchema.model_validate(payload)


def test_create_form_request_contract_accepts_url_information_field():
    payload = _base_create_form_request()
    payload["information_fields"] = [
        {
            "information_field_type": "URL_INFORMATION_FIELD",
            "url": "https://example.com/photo.jpg",
            "mimetype": "image/jpeg",
        }
    ]
    parsed = CreateFormRequestSchema.model_validate(payload)
    assert parsed.information_fields[0].url == "https://example.com/photo.jpg"
    assert parsed.information_fields[0].mimetype == "image/jpeg"


def test_create_form_request_contract_rejects_empty_url_and_mimetype():
    # url/mimetype vazios falham já na camada de contrato (min_length=1),
    # não só depois como EntityError no domínio.
    for field in ("url", "mimetype"):
        payload = _base_create_form_request()
        info = {
            "information_field_type": "URL_INFORMATION_FIELD",
            "url": "https://example.com/photo.jpg",
            "mimetype": "image/jpeg",
        }
        info[field] = ""
        payload["information_fields"] = [info]
        with pytest.raises(ValidationError):
            CreateFormRequestSchema.model_validate(payload)


def test_create_form_response_contract_matches_controller_output():
    repo = FormRepositoryMock()
    file_repo = FileRepositoryMock()
    template_repo = TemplateRepositoryMock()
    controller = CreateFormController(CreateFormUsecase(repo, file_repo, template_repo))

    body = {
        "requester_user": {
            "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "name": "Gabriel Godoy",
            "email": "gabriel@gmail.com",
            "cognito:groups": "FORMULARIOS,GAIA",
        },
        **_base_create_form_request(),
    }

    response = controller(HttpRequest(body=body))
    assert response.status_code == 201
    parsed = CreateFormResponseSchema.model_validate(response.body)
    assert parsed.id == response.body["id"]
    assert parsed.status == "PENDING"


def test_openapi_contract_generator_exposes_create_form_endpoint():
    openapi_doc = build_openapi_from_contracts()
    assert openapi_doc["paths"]["/forms"]["post"]["requestBody"]["required"] is True
    assert "CreateFormRequestSchema" in openapi_doc["components"]["schemas"]
    assert "CreateFormResponseSchema" in openapi_doc["components"]["schemas"]
