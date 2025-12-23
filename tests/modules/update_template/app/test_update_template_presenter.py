import json
import os
import sys

os.environ["STAGE"] = "TEST"
sys.path.append(os.getcwd())

from src.modules.update_template.app.update_template_presenter import lambda_handler, repo


class TestUpdateTemplatePresenter:
    def test_update_template_presenter(self):
        template = repo.templates[0]
        event = {
            "version": "2.0",
            "routeKey": "PUT /templates/{templateId}",
            "rawPath": "/templates/{templateId}",
            "rawQueryString": "",
            "requestContext": {
                "authorizer": {"claims": {"sub": "user-1", "name": "Tester", "email": "t@example.com", "cognito:groups": "FORMULARIOS"}},
            },
            "pathParameters": {"templateId": template.id},
            "body": json.dumps({
                "name": "Presenter Updated",
                "is_active": False
            })
        }

        response = lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_json["name"] == "Presenter Updated"
        assert response_json["is_active"] is False
