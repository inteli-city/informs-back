import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class TestCreateTemplatePresenter:
    def test_create_template_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.create_template.app import create_template_presenter

        importlib.reload(create_template_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/create-template",
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
            "body": {
                "name": "Template X",
                "system": "GAIA",
                "description": "Description",
                "is_active": True,
                "sections": [
                    {
                        "section_id": 1,
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "label": "Name",
                                "required": True,
                                "key": "name",
                                "order": 0,
                            }
                        ],
                    }
                ],
            },
        }

        response = create_template_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 201
        assert response_json["name"] == "Template X"
        assert response_json["system"] == "GAIA"
