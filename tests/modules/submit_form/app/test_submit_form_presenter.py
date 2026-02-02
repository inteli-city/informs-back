import json
import os
import importlib


class Test_SubmitFormPresenter:

    def test_submit_form_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.submit_form.app import submit_form_presenter
        importlib.reload(submit_form_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/my/path",
            "rawQueryString": "parameter1=value1&parameter1=value2&parameter2=value",
            "cookies": [
                "cookie1",
                "cookie2"
            ],
            "headers": {
                "header1": "value1",
                "header2": "value1,value2"
            },
            "queryStringParameters": {
                "parameter1": "1"
            },
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "<urlid>",
                "authentication": None,
                "authorizer": {
                    "claims":
                        {
                            "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                            "name": "Gabriel Godoy",
                            "email": "gabriel@gmail.com",
                            "cognito:groups": "FORMULARIOS"
                        }
                },
                "domainName": "<url-id>.lambda-url.us-west-2.on.aws",
                "domainPrefix": "<url-id>",
                "external_interfaces": {
                    "method": "POST",
                    "path": "/my/path",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "123.123.123.123",
                    "userAgent": "agent"
                },
                "requestId": "id",
                "routeKey": "$default",
                "stage": "$default",
                "time": "12/Mar/2020:19:03:58 +0000",
                "timeEpoch": 1583348638390
            },
            "body": {
                "form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120010",
                "completed_at": 123,
                "sections": [
                    {
                        "section_id": 1,
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "poggers"
                            }
                        ]
                    }
                ]
            },
            "pathParameters": None,
            "isBase64Encoded": None,
            "stageVariables": None
        }

        response = submit_form_presenter.lambda_handler(event, None)

        response_json = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert response_json["files"] == []
