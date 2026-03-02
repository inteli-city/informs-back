import importlib
import json
import os
import sys

sys.path.append(os.getcwd())


class TestSyncFormsOriginCallbackPresenter:
    class _DummyContext:
        function_name = "test-fn"
        memory_limit_in_mb = 128
        invoked_function_arn = "arn:aws:lambda:sa-east-1:000000000000:function:test-fn"
        aws_request_id = "req-123"

    def test_sync_forms_origin_callback_presenter_success(self):
        os.environ["STAGE"] = "TEST"

        from src.modules.sync_forms_origin_callback.app import sync_forms_origin_callback_presenter

        importlib.reload(sync_forms_origin_callback_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/forms/sync-origin/callback",
            "body": {
                "execution_id": "exec-123",
                "form_ids": [
                    "d61dbf66-a10f-11ed-a8fc-0242ac120010",
                    "d61dbf66-a10f-11ed-a8fc-0242ac120011",
                ]
            },
        }

        response = sync_forms_origin_callback_presenter.lambda_handler(event, self._DummyContext())
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        assert "failed_count" not in body
        assert "failed_form_ids" not in body
        assert body["execution_id"] == "exec-123"
        assert len(body["saved_error_forms"]) == 2
        assert body["saved_error_forms"][0]["job_name"] == "sync_forms_origin"

    def test_sync_forms_origin_callback_presenter_bad_request(self):
        os.environ["STAGE"] = "TEST"

        from src.modules.sync_forms_origin_callback.app import sync_forms_origin_callback_presenter

        importlib.reload(sync_forms_origin_callback_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/forms/sync-origin/callback",
            "body": {},
        }

        response = sync_forms_origin_callback_presenter.lambda_handler(event, self._DummyContext())
        body = json.loads(response["body"])

        assert response["statusCode"] == 400
        assert body == "Parâmetro ausente: form_ids"

    def test_sync_forms_origin_callback_presenter_not_found(self):
        os.environ["STAGE"] = "TEST"

        from src.modules.sync_forms_origin_callback.app import sync_forms_origin_callback_presenter

        importlib.reload(sync_forms_origin_callback_presenter)

        event = {
            "version": "2.0",
            "routeKey": "$default",
            "rawPath": "/mss-formularios/forms/sync-origin/callback",
            "body": {"form_ids": ["form-inexistente"]},
        }

        response = sync_forms_origin_callback_presenter.lambda_handler(event, self._DummyContext())
        body = json.loads(response["body"])

        assert response["statusCode"] == 404
        assert "form_ids não encontrados" in body
