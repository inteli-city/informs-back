import os
import sys

import pytest

sys.path.append(os.getcwd())

pytest.importorskip("pydantic")

from src.shared.helpers.contracts.endpoints.sync_origin_callback_contract import (
    SyncCallbackRequestSchema,
    SyncCallbackResponseSchema,
)
from src.shared.helpers.contracts.openapi_contract_generator import build_openapi_from_contracts
from src.shared.helpers.contracts.openapi_contract_registry import get_endpoint_contracts


def test_openapi_contract_registry_covers_http_routes():
    contracts = get_endpoint_contracts()
    registered = {(contract.path, contract.method.lower()) for contract in contracts}

    expected = {
        ("/forms", "post"),
        ("/forms", "get"),
        ("/forms/{formId}", "get"),
        ("/forms/{formId}/start", "post"),
        ("/forms/{formId}/submit", "post"),
        ("/forms/{formId}/files/refresh-presign", "post"),
        ("/forms/{formId}/cancel", "post"),
        ("/forms/route-plan", "post"),
        ("/profiles", "post"),
        ("/profiles/login", "post"),
        ("/profiles/{user_id}", "delete"),
        ("/profiles/{user_id}", "put"),
        ("/templates", "post"),
        ("/templates", "get"),
        ("/templates/{template_id}", "put"),
        ("/templates/{template_id}", "get"),
        ("/forms/sync-origin/callback", "post"),
        ("/locations/history", "get"),
    }

    assert registered == expected


def test_callback_contract_schemas_validate_payloads():
    request_payload = {"form_ids": ["form-1", "form-2"], "execution_id": "exec-123"}
    parsed_request = SyncCallbackRequestSchema.model_validate(request_payload)
    assert parsed_request.form_ids == request_payload["form_ids"]
    assert parsed_request.execution_id == "exec-123"

    response_payload = {
        "received_count": 2,
        "saved_error_forms": [
            {
                "job_name": "sync_forms_origin",
                "system": "GAIA",
                "form_id": "form-1",
                "source_updated_at": None,
                "last_failed_at": 123456,
            }
        ],
        "received_at": 123456,
        "execution_id": "exec-123",
        "message": "Callback completo!",
    }
    parsed_response = SyncCallbackResponseSchema.model_validate(response_payload)
    assert parsed_response.saved_error_forms[0].job_name == "sync_forms_origin"
    assert parsed_response.execution_id == "exec-123"


def test_openapi_contract_generator_exposes_callback_endpoint():
    openapi_doc = build_openapi_from_contracts()
    callback_op = openapi_doc["paths"]["/forms/sync-origin/callback"]["post"]

    assert callback_op["requestBody"]["required"] is True
    assert "SyncCallbackRequestSchema" in openapi_doc["components"]["schemas"]
    assert "SyncCallbackResponseSchema" in openapi_doc["components"]["schemas"]


def test_openapi_contract_keeps_legacy_template_request_field_names():
    openapi_doc = build_openapi_from_contracts()
    create_template_schema = openapi_doc["components"]["schemas"]["CreateTemplateRequestSchema"]
    update_template_schema = openapi_doc["components"]["schemas"]["UpdateTemplateRequestSchema"]

    assert "isActive" in create_template_schema["properties"]
    assert "is_active" not in create_template_schema["properties"]
    assert "isActive" in update_template_schema["properties"]
    assert "is_active" not in update_template_schema["properties"]
