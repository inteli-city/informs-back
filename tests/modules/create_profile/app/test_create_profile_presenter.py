import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"       # ADMIN no mock
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"   # INSPECTOR no mock
NEW_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120099"


def _event(requester_sub: str = ADMIN_USER_ID, groups: str = "FORMULARIOS,GAIA", **body_overrides):
    body = {
        "user_id": NEW_USER_ID,
        "role": "INSPECTOR",
        "name": "New Inspector",
        "email": "new@example.com",
        "system": "GAIA",
    }
    body.update(body_overrides)
    return {
        "version": "2.0",
        "rawPath": "/mss-formularios/profiles",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": requester_sub,
                    "name": "Tester",
                    "email": "tester@example.com",
                    "cognito:groups": groups,
                }
            }
        },
        "body": body,
    }


class TestCreateProfilePresenter:
    def _handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.create_profile.app import create_profile_presenter
        importlib.reload(create_profile_presenter)
        return create_profile_presenter.lambda_handler

    def test_admin_creates_inspector_returns_201(self):
        response = self._handler()(_event(), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 201
        assert body["user_id"] == NEW_USER_ID
        assert body["role"] == "INSPECTOR"
        assert body["active"] is True

    def test_inspector_requester_returns_403(self):
        response = self._handler()(_event(requester_sub=INSPECTOR_USER_ID), None)
        assert response["statusCode"] == 403

    def test_invalid_role_returns_400(self):
        response = self._handler()(_event(role="SUPERADMIN"), None)
        assert response["statusCode"] == 400
