import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml

from src.shared.helpers.contracts.openapi_contract_generator import build_openapi_from_contracts
from src.shared.helpers.contracts.openapi_contract_registry import get_endpoint_contracts

REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_doc(path: Path) -> Dict[str, Any]:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text())
    return yaml.safe_load(path.read_text()) or {}


def _resolve_pointer(doc: Dict[str, Any], ref: str) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"Only local refs are supported: {ref}")
    current: Any = doc
    for raw in ref[2:].split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        current = current[part]
    if not isinstance(current, dict):
        return {}
    return current


def _resolve_schema(doc: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return {}
    if "$ref" in schema:
        target = _resolve_pointer(doc, schema["$ref"])
        extra = {key: value for key, value in schema.items() if key != "$ref"}
        if not extra:
            return target
        merged = dict(target)
        merged.update(extra)
        return merged
    return schema


def _collect_object_shape(
    doc: Dict[str, Any],
    schema: Dict[str, Any],
    properties: Set[str],
    required: Set[str],
) -> None:
    schema = _resolve_schema(doc, schema)
    if not schema:
        return

    composed = schema.get("allOf")
    if isinstance(composed, list):
        for sub_schema in composed:
            if isinstance(sub_schema, dict):
                _collect_object_shape(doc, sub_schema, properties, required)

    schema_props = schema.get("properties", {})
    if isinstance(schema_props, dict):
        properties.update(schema_props.keys())

    schema_required = schema.get("required", [])
    if isinstance(schema_required, list):
        required.update(item for item in schema_required if isinstance(item, str))


def _extract_schema_from_operation(operation: Dict[str, Any], success_status_code: int, is_request: bool) -> Dict[str, Any]:
    if is_request:
        request_body = operation.get("requestBody", {})
        return request_body.get("content", {}).get("application/json", {}).get("schema", {}) or {}
    return (
        operation.get("responses", {})
        .get(str(success_status_code), {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        or {}
    )


def _compare_shapes(
    source_name: str,
    path: str,
    method: str,
    contract_shape: Tuple[Set[str], Set[str]],
    merged_shape: Tuple[Set[str], Set[str]],
    errors: List[str],
    compare_required: bool = True,
) -> None:
    contract_properties, contract_required = contract_shape
    merged_properties, merged_required = merged_shape

    missing_in_merged = contract_properties - merged_properties
    extra_in_merged = merged_properties - contract_properties
    if missing_in_merged:
        errors.append(
            f"[{source_name}] {method.upper()} {path}: missing properties in merged spec: {sorted(missing_in_merged)}"
        )
    if extra_in_merged:
        errors.append(
            f"[{source_name}] {method.upper()} {path}: extra properties in merged spec: {sorted(extra_in_merged)}"
        )

    if compare_required:
        missing_required_in_merged = contract_required - merged_required
        if missing_required_in_merged:
            errors.append(
                f"[{source_name}] {method.upper()} {path}: merged spec is weaker for required fields: {sorted(missing_required_in_merged)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check drift between code-first contracts and merged OpenAPI YAML")
    parser.add_argument(
        "--merged-openapi",
        default=str(REPO_ROOT / "src" / "modules" / "docs" / "app" / "swagger.merged.yaml"),
        help="Path to merged OpenAPI (YAML/JSON)",
    )
    args = parser.parse_args()

    merged_doc = _load_doc(Path(args.merged_openapi).resolve())
    contracts_doc = build_openapi_from_contracts()

    errors: List[str] = []
    contracts = get_endpoint_contracts()

    for contract in contracts:
        path = contract.path
        method = contract.method.lower()
        status_code = contract.success_status_code

        contract_op = contracts_doc.get("paths", {}).get(path, {}).get(method)
        merged_op = merged_doc.get("paths", {}).get(path, {}).get(method)
        if contract_op is None:
            errors.append(f"[operation] Missing operation in contracts doc: {method.upper()} {path}")
            continue
        if merged_op is None:
            errors.append(f"[operation] Missing operation in merged doc: {method.upper()} {path}")
            continue

        contract_request_schema = _extract_schema_from_operation(contract_op, status_code, is_request=True)
        merged_request_schema = _extract_schema_from_operation(merged_op, status_code, is_request=True)
        if contract_request_schema:
            c_props: Set[str] = set()
            c_req: Set[str] = set()
            m_props: Set[str] = set()
            m_req: Set[str] = set()
            _collect_object_shape(contracts_doc, contract_request_schema, c_props, c_req)
            _collect_object_shape(merged_doc, merged_request_schema, m_props, m_req)
            _compare_shapes("request", path, method, (c_props, c_req), (m_props, m_req), errors, compare_required=True)

        contract_response_schema = _extract_schema_from_operation(contract_op, status_code, is_request=False)
        merged_response_schema = _extract_schema_from_operation(merged_op, status_code, is_request=False)
        if contract_response_schema:
            c_props = set()
            c_req = set()
            m_props = set()
            m_req = set()
            _collect_object_shape(contracts_doc, contract_response_schema, c_props, c_req)
            _collect_object_shape(merged_doc, merged_response_schema, m_props, m_req)
            _compare_shapes("response", path, method, (c_props, c_req), (m_props, m_req), errors, compare_required=False)

    if errors:
        print("OpenAPI contract drift detected:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("OpenAPI contract drift check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
