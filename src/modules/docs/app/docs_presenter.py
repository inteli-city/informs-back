import json
import os
from pathlib import Path

import yaml

JSON_PATH_SUFFIXES = ("/docs/json", "/docs/swagger.json", "/docs/openapi.json")
JSON_QUERY_KEYS = ("format", "output")
DEFAULT_SWAGGER_FILES = ("swagger.merged.yaml", "swagger.json", "swagger.contracts.json")

def _get_request_path(event: dict) -> str:
    if not event:
        return ""
    return (
        event.get("rawPath")
        or event.get("path")
        or event.get("requestContext", {}).get("http", {}).get("path", "")
    )


def _get_query_params(event: dict) -> dict:
    if not event:
        return {}
    return event.get("queryStringParameters") or {}


def _should_return_json_by_query(params: dict) -> bool:
    if not params:
        return False
    for key in JSON_QUERY_KEYS:
        value = params.get(key)
        if isinstance(value, str) and value.lower() in {"json", "swagger", "openapi"}:
            return True
    return False


def _should_return_json(path: str) -> bool:
    if not path:
        return False
    normalized = path.rstrip("/")
    return normalized.endswith(JSON_PATH_SUFFIXES)


def _load_swagger_content() -> str:
    custom_file = os.getenv("SWAGGER_DOC_FILE")
    candidates = [custom_file] if custom_file else []
    candidates.extend(DEFAULT_SWAGGER_FILES)

    docs_dir = Path(__file__).resolve().parent
    tried_files = []

    for filename in candidates:
        if not filename:
            continue
        file_path = docs_dir / filename
        tried_files.append(str(file_path.name))
        if not file_path.exists():
            continue

        raw_content = file_path.read_text()
        if file_path.suffix in {".yaml", ".yml"}:
            parsed = yaml.safe_load(raw_content) or {}
            return json.dumps(parsed, ensure_ascii=True)

        parsed = json.loads(raw_content)
        return json.dumps(parsed, ensure_ascii=True)

    raise FileNotFoundError(f"Swagger documentation not found. Tried: {', '.join(tried_files)}")

def lambda_handler(event, context):
    try:
        swagger_content = _load_swagger_content()
    except FileNotFoundError:
        return {
            "statusCode": 500,
            "body": "Swagger documentation not found."
        }
    except Exception as e:
        print(f"Erro ao ler swagger.json: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Erro interno: Arquivo de documentação não encontrado."})
        }
    
    request_path = _get_request_path(event)
    query_params = _get_query_params(event)
    if _should_return_json_by_query(query_params) or _should_return_json(request_path):
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": swagger_content
        }

    

    html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Informs API Docs</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
        <style>
            body {{ margin: 0; padding: 0; }}
            .swagger-ui .topbar {{ display: none; }} 
        </style>
        </head>
        <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" crossorigin></script>
        <script>
            window.onload = () => {{
            window.ui = SwaggerUIBundle({{
                spec: {swagger_content}, 
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            }});
            }};
        </script>
        </body>
        </html>
    """

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html",
            "Access-Control-Allow-Origin": "*"
        },
        "body": html
    }
