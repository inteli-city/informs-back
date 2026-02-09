import json
import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPENAPI_ROOT = ROOT / "src" / "modules" / "docs" / "app" / "openapi" / "openapi.yaml"

_YAML_CACHE: Dict[str, Any] = {}


def _load_yaml(path: Path) -> Any:
    cache_key = str(path.resolve())
    if cache_key in _YAML_CACHE:
        return _YAML_CACHE[cache_key]
    with path.open("r") as file:
        data = yaml.safe_load(file) or {}
    _YAML_CACHE[cache_key] = data
    return data


def _resolve_pointer(doc: Any, pointer: str) -> Any:
    if not pointer:
        return doc
    if pointer.startswith("/"):
        pointer = pointer[1:]
    current = doc
    for raw_part in pointer.split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def _resolve_ref(ref: str, base_path: Path, stack: List[str]) -> Any:
    file_part, fragment = (ref.split("#", 1) + [""])[:2]
    target_path = (base_path.parent / file_part).resolve() if file_part else base_path.resolve()
    stack_key = f"{target_path}#{fragment}"
    if stack_key in stack:
        raise ValueError(f"Circular $ref detected: {stack_key}")
    doc = _load_yaml(target_path)
    target = doc
    if fragment:
        target = _resolve_pointer(doc, fragment if fragment.startswith("/") else f"/{fragment}")
    return _resolve_refs(target, target_path, stack + [stack_key])


def _resolve_refs(obj: Any, base_path: Path, stack: List[str]) -> Any:
    if isinstance(obj, dict):
        if "$ref" in obj:
            resolved = _resolve_ref(obj["$ref"], base_path, stack)
            if len(obj) == 1:
                return resolved
            merged = deepcopy(resolved) if isinstance(resolved, dict) else {"value": resolved}
            for key, value in obj.items():
                if key == "$ref":
                    continue
                merged[key] = _resolve_refs(value, base_path, stack)
            return merged
        return {key: _resolve_refs(value, base_path, stack) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_resolve_refs(item, base_path, stack) for item in obj]
    return obj


def _find_openapi_root() -> Path:
    candidates = [
        DEFAULT_OPENAPI_ROOT,
        ROOT / "app" / "openapi" / "openapi.yaml",
        Path.cwd() / "src" / "modules" / "docs" / "app" / "openapi" / "openapi.yaml",
        Path.cwd() / "app" / "openapi" / "openapi.yaml",
        Path.cwd() / "openapi" / "openapi.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "OpenAPI root not found. Provide --openapi-root or place openapi.yaml in a known location."
    )


def _default_output_for(openapi_root: Path) -> Path:
    return openapi_root.parent.parent / "swagger.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge OpenAPI YAMLs into swagger.json")
    parser.add_argument("--openapi-root", dest="openapi_root", help="Path to openapi.yaml")
    parser.add_argument("--output", dest="output", help="Path to output swagger.json")
    parser.add_argument("--yaml-output", dest="yaml_output", help="Path to output swagger.merged.yaml")
    args = parser.parse_args()

    openapi_root = Path(args.openapi_root).resolve() if args.openapi_root else _find_openapi_root()
    if not openapi_root.exists():
        raise FileNotFoundError(f"OpenAPI root not found: {openapi_root}")

    output = Path(args.output).resolve() if args.output else _default_output_for(openapi_root)
    yaml_output = Path(args.yaml_output).resolve() if args.yaml_output else output.with_name("swagger.merged.yaml")

    root_doc = _load_yaml(openapi_root)
    merged = _resolve_refs(root_doc, openapi_root, [])
    output.write_text(json.dumps(merged, ensure_ascii=True))
    yaml_output.write_text(yaml.safe_dump(merged, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
