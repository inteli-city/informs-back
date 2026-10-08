import importlib
import json
import os
import sys

sys.path.append(os.getcwd())

PLATFORM_ADMIN = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


def _event(user_id, body=None, path_parameters=None):
    event = {
        "requestContext": {
            "authorizer": {
                "claims": {"sub": user_id, "name": "User", "email": "user@test.com", "cognito:groups": "FORMULARIOS,GAIA"}
            }
        },
    }
    if body is not None:
        event["body"] = json.dumps(body)
    if path_parameters:
        event["pathParameters"] = path_parameters
    return event


def _load(module):
    os.environ["STAGE"] = "TEST"
    presenter = importlib.import_module(f"src.modules.{module}.app.{module}_presenter")
    return importlib.reload(presenter)


class TestAppConfigAdminPresenters:
    def test_get_admin_returns_schema_and_layers(self):
        presenter = _load("get_app_config_admin")
        response = presenter.lambda_handler(_event(PLATFORM_ADMIN), None)
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["can_edit_default"] is True
        assert body["config_schema"]["properties"]["menus"]["title"] == "Menus"
        assert body["schema_defaults"]["menus"]["create_form"] is True
        assert [item["system"] for item in body["systems"]] == ["GAIA"]

    def test_get_admin_forbidden_for_plain_inspector(self):
        presenter = _load("get_app_config_admin")
        response = presenter.lambda_handler(_event(INSPECTOR), None)
        assert response["statusCode"] == 403

    def test_put_default_then_conflict_on_stale_version(self):
        presenter = _load("put_default_app_config")
        first = presenter.lambda_handler(_event(PLATFORM_ADMIN, {"values": {"menus": {"route_plan": False}}, "base_version": 0}), None)
        second = presenter.lambda_handler(_event(PLATFORM_ADMIN, {"values": {}, "base_version": 0}), None)

        assert first["statusCode"] == 200
        assert json.loads(first["body"])["version"] == 1
        assert second["statusCode"] == 409

    def test_put_default_rejects_invalid_layer(self):
        presenter = _load("put_default_app_config")
        response = presenter.lambda_handler(_event(PLATFORM_ADMIN, {"values": {"menus": {"nope": 1}}, "base_version": 0}), None)
        assert response["statusCode"] == 400

    def test_put_system_reads_system_from_path(self):
        presenter = _load("put_system_app_config")
        response = presenter.lambda_handler(
            _event(PLATFORM_ADMIN, {"values": {"flows": {"cancel_form": True}}, "base_version": 0}, {"system": "GAIA"}), None
        )
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert body["system"] == "GAIA"
        assert body["effective"]["flows"]["cancel_form"] is True
