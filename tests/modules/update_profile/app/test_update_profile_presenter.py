import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"       # ADMIN no mock
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"   # INSPECTOR no mock


def _event(requester_sub: str, target_user_id: str, role: str, scope=None, groups: str = "FORMULARIOS,GAIA"):
    return {
        "version": "2.0",
        "rawPath": f"/mss-formularios/profiles/{target_user_id}",
        "pathParameters": {"user_id": target_user_id},
        "body": {"role": role, "scope": scope if scope is not None else {}},
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
    }


class TestUpdateProfilePresenter:
    def _handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.update_profile.app import update_profile_presenter
        importlib.reload(update_profile_presenter)
        return update_profile_presenter.lambda_handler

    def test_admin_updates_inspector_returns_200(self):
        response = self._handler()(
            _event(ADMIN_USER_ID, INSPECTOR_USER_ID, role="MANAGER", scope={"bairro": ["Santa Mônica"]}), None
        )
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["user_id"] == INSPECTOR_USER_ID
        assert body["role"] == "MANAGER"
        assert body["scope"] == {"bairro": ["Santa Mônica"]}

    def test_inspector_requester_returns_403(self):
        response = self._handler()(
            _event(INSPECTOR_USER_ID, ADMIN_USER_ID, role="MANAGER"), None
        )
        assert response["statusCode"] == 403

    def test_target_not_found_returns_404(self):
        response = self._handler()(
            _event(ADMIN_USER_ID, "d61dbf66-a10f-11ed-a8fc-0242ac129999", role="MANAGER"), None
        )
        assert response["statusCode"] == 404
