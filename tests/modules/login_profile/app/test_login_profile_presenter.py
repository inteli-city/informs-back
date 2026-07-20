import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"   # já existe no mock
NEW_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120099"     # não existe -> auto-cria


def _event(sub: str, groups: str = "FORMULARIOS,GAIA"):
    return {
        "version": "2.0",
        "rawPath": "/mss-formularios/profiles/login",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "sub": sub,
                    "name": "Tester",
                    "email": "tester@example.com",
                    "cognito:groups": groups,
                }
            }
        },
    }


class TestLoginProfilePresenter:
    def _handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.login_profile.app import login_profile_presenter
        importlib.reload(login_profile_presenter)
        return login_profile_presenter.lambda_handler

    def test_existing_profile_returns_200_not_created(self):
        response = self._handler()(_event(ADMIN_USER_ID), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["user_id"] == ADMIN_USER_ID
        assert body["just_created"] is False

    def test_new_user_autocreated_as_inspector(self):
        response = self._handler()(_event(NEW_USER_ID), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["user_id"] == NEW_USER_ID
        assert body["just_created"] is True
        assert body["role"] == "INSPECTOR"
