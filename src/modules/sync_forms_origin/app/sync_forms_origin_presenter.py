import time
from typing import Dict, List

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit, single_metric

from src.shared.environments import Environments
from src.shared.helpers.external_interfaces.event_bridge_requests import LambdaEventBridgeRequest
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpResponse
from .sync_forms_origin_usecase import SyncFormsOriginUsecase


SYSTEM_TO_ORIGIN = {
    "GAIA": "gaia",
    "GIPAV": "servicos_poa",
}

SERVICE_NAME = "sync_forms_origin"
METRICS_NAMESPACE = "Informs"

logger = Logger(service=SERVICE_NAME)
metrics = Metrics(namespace=METRICS_NAMESPACE, service=SERVICE_NAME)
tracer = Tracer(service=SERVICE_NAME)

form_repo = Environments.get_form_repo()
origin_repo = Environments.get_origin_repo()
sync_state_repo = Environments.get_sync_state_repo()
sync_error_form_repo = Environments.get_sync_error_form_repo()
usecase = SyncFormsOriginUsecase(
    form_repo=form_repo,
    origin_repo=origin_repo,
    sync_state_repo=sync_state_repo,
    sync_error_form_repo=sync_error_form_repo,
)


def _parse_systems() -> List[str]:
    raw = Environments.get_envs().sync_forms_origin_systems
    return [item.strip().upper() for item in raw.split(",") if item.strip()]

def _summarize_results(results, error_limit: int = 5) -> List[Dict[str, object]]:
    summaries: List[Dict[str, object]] = []
    for result in results:
        errors = result.errors or []
        summaries.append(
            {
                "system": result.system,
                "execution_id": result.execution_id,
                "sent": result.sent,
                "failed": result.failed,
                "pages_loaded": result.pages_loaded,
                "forms_loaded": result.forms_loaded,
                "previous_synced_at": result.previous_synced_at,
                "new_synced_at": result.new_synced_at,
                "sync_started_at": result.sync_started_at,
                "sync_ended_at": result.sync_ended_at,
                "start_cursor_fingerprint": result.start_cursor_fingerprint,
                "end_cursor_fingerprint": result.end_cursor_fingerprint,
                "errors_count": len(errors),
                "errors_sample": errors[:error_limit] if errors else None,
            }
        )
    return summaries


@logger.inject_lambda_context(clear_state=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    start_time = time.time()
    envs = Environments.get_envs()
    page_size = envs.sync_forms_page_limit
    bootstrap_window_minutes = envs.sync_forms_window_minutes
    full_sync_on_first_run = envs.sync_forms_first_run_full_sync
    systems = _parse_systems()

    event_request = LambdaEventBridgeRequest(event)
    logger.info(
        "sync_forms_origin triggered",
        extra={
            "event": event_request.summary(),
            "requested_systems": systems,
            "bootstrap_window_minutes": bootstrap_window_minutes,
            "page_size": page_size,
            "full_sync_on_first_run": full_sync_on_first_run,
        },
    )

    results = usecase(
        systems=systems,
        system_mapping=SYSTEM_TO_ORIGIN,
        bootstrap_window_minutes=bootstrap_window_minutes,
        page_size=page_size,
        full_sync_on_first_run=full_sync_on_first_run,
        logger=logger,
    )

    total_sent = sum(result.sent for result in results)
    total_failed = sum(result.failed for result in results)
    total_processed = total_sent + total_failed
    duration_ms = int((time.time() - start_time) * 1000)

    metrics.add_metric("FormsSent", MetricUnit.Count, total_sent)
    metrics.add_metric("FormsFailed", MetricUnit.Count, total_failed)
    metrics.add_metric("FormsProcessed", MetricUnit.Count, total_processed)
    metrics.add_metric("SyncDurationMs", MetricUnit.Milliseconds, duration_ms)

    for result in results:
        with single_metric(
            name="FormsSentBySystem",
            unit=MetricUnit.Count,
            value=result.sent,
            namespace=METRICS_NAMESPACE,
            default_dimensions={"service": SERVICE_NAME, "system": result.system},
        ):
            pass
        with single_metric(
            name="FormsFailedBySystem",
            unit=MetricUnit.Count,
            value=result.failed,
            namespace=METRICS_NAMESPACE,
            default_dimensions={"service": SERVICE_NAME, "system": result.system},
        ):
            pass

    summary = _summarize_results(results)
    logger.info(
        "sync_forms_origin completed",
        extra={
            "duration_ms": duration_ms,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "results": summary,
        },
    )

    payload = {
        "requested_systems": systems,
        "bootstrap_window_minutes": bootstrap_window_minutes,
        "page_size": page_size,
        "full_sync_on_first_run": full_sync_on_first_run,
        "duration_ms": duration_ms,
        "totals": {
            "sent": total_sent,
            "failed": total_failed,
            "processed": total_processed,
        },
        "results": [result.__dict__ for result in results],
    }

    return LambdaHttpResponse(status_code=200, body=payload).toDict()
