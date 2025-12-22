import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class TestGetTemplatePresenter:
    def test_get_template_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_template.app import get_template_presenter

        importlib.reload(get_template_presenter)

        template = get_template_presenter.repo.templates[0]

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": f"/mss-formularios/templates/{template.id}",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS",
                    }
                }
            },
            "pathParameters": {"template_id": template.id},
        }

        response = get_template_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_json["id"] == template.id
