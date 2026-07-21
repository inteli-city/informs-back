import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"       # ADMIN no mock
INSPECTOR_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"   # INSPECTOR no mock
TARGET = "fake-inspector-id"                            # tem pings no location mock


def _event(requester_sub: str = ADMIN_ID, groups: str = "FORMULARIOS,GAIA", query=None):
    query = query if query is not None else {"user_id": TARGET, "since": "1", "until": "10000"}
    return {
        "version": "2.0",
        "rawPath": "/mss-formularios/locations/history",
        "queryStringParameters": query,
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


class TestGetLocationHistoryPresenter:
    def _handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.get_location_history.app import get_location_history_presenter
        importlib.reload(get_location_history_presenter)
        return get_location_history_presenter.lambda_handler

    def test_admin_returns_200_with_pings(self):
        response = self._handler()(_event(), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["count"] == len(body["items"])
        assert body["count"] >= 1

    def test_inspector_requester_returns_403(self):
        response = self._handler()(_event(requester_sub=INSPECTOR_ID), None)
        assert response["statusCode"] == 403

    def test_missing_user_id_returns_400(self):
        response = self._handler()(_event(query={"since": "1", "until": "10000"}), None)
        assert response["statusCode"] == 400
