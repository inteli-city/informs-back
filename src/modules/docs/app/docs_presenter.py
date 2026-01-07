import json
from pathlib import Path

def lambda_handler(event, context):
    try:
        swagger_path = Path(__file__).with_name("swagger.json")
        with swagger_path.open("r") as file:
            swagger_content = file.read()
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
