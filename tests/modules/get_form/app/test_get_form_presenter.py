import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class Test_GetFormPresenter:
    def test_get_form_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_form.app import get_form_presenter
        importlib.reload(get_form_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/forms/get",
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
                "form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120010"
            }
        }

        response = get_form_presenter.lambda_handler(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["id"] == "d61dbf66-a10f-11ed-a8fc-0242ac120010"
