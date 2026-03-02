import argparse
import json
from pathlib import Path

from src.shared.helpers.contracts.openapi_contract_generator import build_openapi_from_contracts

REPO_ROOT = Path(__file__).resolve().parents[4]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenAPI JSON from Pydantic endpoint contracts")
    parser.add_argument(
        "--json-output",
        default=str(REPO_ROOT / "src" / "modules" / "docs" / "app" / "swagger.json"),
        help="Main output file for generated OpenAPI JSON",
    )
    parser.add_argument(
        "--contracts-json-output",
        default=str(REPO_ROOT / "src" / "modules" / "docs" / "app" / "swagger.contracts.json"),
        help="Secondary output file for generated OpenAPI JSON (legacy contracts filename)",
    )
    args = parser.parse_args()

    openapi_doc = build_openapi_from_contracts()
    json_path = Path(args.json_output).resolve()
    contracts_json_path = Path(args.contracts_json_output).resolve()

    json_path.parent.mkdir(parents=True, exist_ok=True)
    contracts_json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(openapi_doc, ensure_ascii=True))
    contracts_json_path.write_text(json.dumps(openapi_doc, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
