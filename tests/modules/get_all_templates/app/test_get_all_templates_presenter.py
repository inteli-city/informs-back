import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class TestGetAllTemplatesPresenter:
    def test_get_all_templates_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_all_templates.app import get_all_templates_presenter

        importlib.reload(get_all_templates_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/templates",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS,GAIA",
                    }
                }
            },
            "queryStringParameters": {"limit": 20, "isActive": True, "system": "GAIA"},
        }

        response = get_all_templates_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "templates" in response_json
        assert response_json["limit"] == 20
        assert response_json["system"] == "GAIA"
