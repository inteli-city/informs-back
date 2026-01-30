import importlib
import os
import json
import sys

sys.path.append(os.getcwd())


class Test_GetAllFormsPresenter:
    def test_get_all_forms_presenter(self):
        os.environ["STAGE"] = "TEST"
        # ensure module picks STAGE=TEST
        from src.modules.get_all_forms.app import get_all_forms_presenter
        importlib.reload(get_all_forms_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/get-all-forms",
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
            "queryStringParameters": {
                "limit": 20,
                "status": "PENDING"
            }
        }

        response = get_all_forms_presenter.lambda_handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "forms" in body
        assert body["limit"] == 20
        assert body["last_evaluated_key"] is None

    def test_get_all_forms_presenter_status_list(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_all_forms.app import get_all_forms_presenter
        importlib.reload(get_all_forms_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/get-all-forms",
            "rawQueryString": "status=PENDING&status=IN_PROGRESS&limit=20",
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
            "queryStringParameters": {
                "limit": "20"
            }
        }

        response = get_all_forms_presenter.lambda_handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        statuses = {item["status"] for item in body["forms"]}
        assert statuses == {"PENDING", "IN_PROGRESS"}
