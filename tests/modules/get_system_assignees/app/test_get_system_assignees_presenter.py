import importlib
import json
import os

from src.shared.infra.repositories.profile_repository_mock import MOCK_SUPER_ADMIN_ID


def _event(user_id: str) -> dict:
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": "/systems/GAIA/assignees",
        "headers": {},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": user_id,
                    "name": "Super Admin",
                    "email": "super@example.com",
                    "cognito:groups": "FORMULARIOS",
                }
            },
            "external_interfaces": {"method": "GET", "path": "/systems/GAIA/assignees"},
        },
        "pathParameters": {"system": "GAIA"},
        "queryStringParameters": None,
        "body": None,
        "isBase64Encoded": None,
        "stageVariables": None,
    }


class TestGetSystemAssigneesPresenter:

    def test_get_system_assignees_presenter(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_system_assignees.app import get_system_assignees_presenter
        importlib.reload(get_system_assignees_presenter)

        response = get_system_assignees_presenter.lambda_handler(_event(MOCK_SUPER_ADMIN_ID), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["system"] == "GAIA"
        assert all(user["user_id"] != MOCK_SUPER_ADMIN_ID for user in body["users"])
        assert all("email" not in user for user in body["users"])
