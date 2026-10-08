import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class TestGetAppConfigPresenter:
    def test_get_app_config_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_app_config.app import get_app_config_presenter

        importlib.reload(get_app_config_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/app-config",
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "sub": "user-123",
                        "name": "User",
                        "email": "user@test.com",
                        "cognito:groups": "FORMULARIOS,GAIA,UBERLANDIA",
                    }
                }
            },
        }

        response = get_app_config_presenter.lambda_handler(event, None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert [item["system"] for item in body["systems"]] == ["GAIA", "UBERLANDIA"]
        assert body["default"]["config"]["menus"]["create_form"] is True
