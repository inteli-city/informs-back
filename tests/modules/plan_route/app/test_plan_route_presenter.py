import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


REQUESTER_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"


def _event(sub: str = REQUESTER_USER_ID, groups: str = "FORMULARIOS", **body_overrides):
    body = {
        "start": {"latitude": -23.56, "longitude": -46.65},
        "n": 5,
    }
    body.update(body_overrides)
    return {
        "version": "2.0",
        "rawPath": "/mss-formularios/forms/route-plan",
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
        "body": body,
    }


class TestPlanRoutePresenter:
    def _handler(self):
        os.environ["STAGE"] = "TEST"
        from src.modules.plan_route.app import plan_route_presenter
        importlib.reload(plan_route_presenter)
        return plan_route_presenter.lambda_handler

    def test_returns_200_with_ordered_forms(self):
        response = self._handler()(_event(), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "ordered_forms" in body
        assert "total_distance_km" in body
        assert isinstance(body["ordered_forms"], list)

    def test_invalid_n_returns_400(self):
        response = self._handler()(_event(n=0), None)
        assert response["statusCode"] == 400
