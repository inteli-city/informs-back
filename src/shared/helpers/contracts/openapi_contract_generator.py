from copy import deepcopy
from typing import Any, Dict, Iterable, Type

from pydantic import BaseModel

from src.shared.helpers.contracts.openapi_contract_registry import EndpointContract, get_endpoint_contracts


def _rewrite_refs(node: Any) -> Any:
    if isinstance(node, dict):
        rewritten = {}
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str) and value.startswith("#/$defs/"):
                rewritten[key] = value.replace("#/$defs/", "#/components/schemas/")
            else:
                rewritten[key] = _rewrite_refs(value)
        return rewritten
    if isinstance(node, list):
        return [_rewrite_refs(item) for item in node]
    return node


def _collect_models(contracts: Iterable[EndpointContract]) -> list[Type[BaseModel]]:
    models: Dict[str, Type[BaseModel]] = {}
    for contract in contracts:
        if contract.request_model is not None:
            models[contract.request_model.__name__] = contract.request_model
        if contract.response_model is not None:
            models[contract.response_model.__name__] = contract.response_model
    return list(models.values())


def _build_components(models: Iterable[Type[BaseModel]]) -> dict:
    schemas: dict = {}
    for model in models:
        model_schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        model_schema = _rewrite_refs(model_schema)
        defs = model_schema.pop("$defs", {})

        schemas[model.__name__] = model_schema
        for def_name, def_schema in defs.items():
            if def_name not in schemas:
                schemas[def_name] = _rewrite_refs(def_schema)
    return {"schemas": schemas}


def _build_paths(contracts: Iterable[EndpointContract]) -> dict:
    paths = {}
    for contract in contracts:
        path_item = deepcopy(paths.get(contract.path, {}))
        operation = {
            "summary": contract.summary,
            "tags": [contract.tag],
            "responses": {
                str(contract.success_status_code): {
                    "description": "Success",
                }
            },
        }

        if contract.request_model is not None:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{contract.request_model.__name__}"}
                    }
                },
            }

        if contract.response_model is not None:
            operation["responses"][str(contract.success_status_code)]["content"] = {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{contract.response_model.__name__}"}
                }
            }

        path_item[contract.method.lower()] = operation
        paths[contract.path] = path_item
    return paths


def build_openapi_from_contracts() -> dict:
    contracts = get_endpoint_contracts()
    models = _collect_models(contracts)
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Informs Contracts (Code-first)",
            "version": "1.0.0",
        },
        "paths": _build_paths(contracts),
        "components": _build_components(models),
    }
