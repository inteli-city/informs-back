import argparse
import json
from pathlib import Path

import yaml

from src.shared.helpers.contracts.openapi_contract_generator import build_openapi_from_contracts

REPO_ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenAPI from Pydantic endpoint contracts")
    parser.add_argument(
        "--json-output",
        default=str(REPO_ROOT / "src" / "modules" / "docs" / "app" / "swagger.contracts.json"),
        help="Output file for generated OpenAPI JSON",
    )
    parser.add_argument(
        "--yaml-output",
        default=str(REPO_ROOT / "src" / "modules" / "docs" / "app" / "swagger.contracts.yaml"),
        help="Output file for generated OpenAPI YAML",
    )
    args = parser.parse_args()

    openapi_doc = build_openapi_from_contracts()
    json_path = Path(args.json_output).resolve()
    yaml_path = Path(args.yaml_output).resolve()

    json_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(openapi_doc, ensure_ascii=True))
    yaml_path.write_text(yaml.safe_dump(openapi_doc, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
