import importlib
import json
import os
import sys

import pytest

sys.path.append(os.getcwd())


class TestSyncFormsOriginPresenter:
    class _DummyContext:
        function_name = "sync-forms-origin"
        memory_limit_in_mb = 512
        invoked_function_arn = "arn:aws:lambda:sa-east-1:000000000000:function:sync-forms-origin"
        aws_request_id = "req-sync-1"

    def _handler(self):
        os.environ["STAGE"] = "TEST"
        os.environ.setdefault("POWERTOOLS_TRACE_DISABLED", "1")
        try:
            from src.modules.sync_forms_origin.app import sync_forms_origin_presenter
            importlib.reload(sync_forms_origin_presenter)
        except ModuleNotFoundError as err:
            # O presenter importa aws_lambda_powertools.Tracer -> aws_xray_sdk ->
            # botocore.docs -> cgi (removido no Python 3.13). Fora do runtime
            # Lambda (ex.: dev local em 3.13) o módulo não importa; no CI
            # (Python 3.10) roda normalmente.
            pytest.skip(f"ambiente sem suporte a import do presenter: {err}")
        return sync_forms_origin_presenter.lambda_handler

    def test_scheduled_event_runs_and_returns_200(self):
        event = {
            "version": "0",
            "id": "sched-1",
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "region": "sa-east-1",
            "detail": {},
        }

        response = self._handler()(event, self._DummyContext())
        body = json.loads(response["body"])

        assert response["statusCode"] == 200
        # roda para todos os sistemas mapeados (GAIA, GIPAV)
        assert body["requested_systems"] == ["GAIA", "GIPAV"]
        assert "totals" in body
        assert body["totals"]["processed"] == body["totals"]["sent"] + body["totals"]["failed"]
        assert len(body["results"]) == len(body["requested_systems"])
