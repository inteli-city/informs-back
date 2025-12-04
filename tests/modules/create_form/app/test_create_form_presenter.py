import json
import os
import sys
import importlib

sys.path.append(os.getcwd())


class Test_CreateFormPresenter:
    def test_create_form_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.create_form.app import create_form_presenter
        importlib.reload(create_form_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/create-form",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS"
                    }
                }
            },
            "body": {
                "form_title": "FORM TITLE",
                "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "system": "GAIA",
                "street": "1",
                "city": "1",
                "latitude": 1.0,
                "longitude": 1.0,
                "priority": "EMERGENCY",
                "justifications": [
                    {"option": "option", "required_image": True, "required_text": True}
                ],
                "sessions": [
                    {
                        "section_id": 1,
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "label": "placeholder",
                                "required": True,
                                "key": "key",
                                "order": 0
                            }
                        ]
                    }
                ],
                "information_fields": [
                    {
                        "information_field_type": "TEXT_INFORMATION_FIELD",
                        "value": "value"
                    }
                ]
            }
        }

        response = create_form_presenter.lambda_handler(event, None)
        response_json = json.loads(response["body"])

        assert response["statusCode"] == 201
        assert response_json["form_title"] == "FORM TITLE"
        assert response_json["status"] == "PENDING"
