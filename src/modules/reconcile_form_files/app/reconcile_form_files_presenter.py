import time

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit, single_metric

from src.shared.environments import Environments
from src.shared.helpers.external_interfaces.event_bridge_requests import LambdaEventBridgeRequest
from src.shared.helpers.external_interfaces.http_lambda_requests import LambdaHttpResponse
from .reconcile_form_files_usecase import ReconcileFormFilesUsecase


SERVICE_NAME = "reconcile_form_files"
METRICS_NAMESPACE = "Informs"

logger = Logger(service=SERVICE_NAME)
metrics = Metrics(namespace=METRICS_NAMESPACE, service=SERVICE_NAME)
tracer = Tracer(service=SERVICE_NAME)

form_repo = Environments.get_form_repo()
file_repo = Environments.get_file_repo()
usecase = ReconcileFormFilesUsecase(form_repo=form_repo, file_repo=file_repo)


def _int_or_none(event: dict, key: str):
    """
    Os parâmetros de janela vêm do evento para permitir backfill sob demanda
    (invoke manual com created_at_start/created_at_end) sem mudar o schedule.
    """
    value = event.get(key) if isinstance(event, dict) else None
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("parametro ignorado por nao ser inteiro", extra={"param": key, "value": str(value)})
        return None


@logger.inject_lambda_context(clear_state=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    start_time = time.time()
    event = event if isinstance(event, dict) else {}

    event_request = LambdaEventBridgeRequest(event)
    logger.info("reconcile_form_files triggered", extra={"event": event_request.summary()})

    result = usecase(
        created_at_start=_int_or_none(event, "created_at_start"),
        created_at_end=_int_or_none(event, "created_at_end"),
        window_hours=_int_or_none(event, "window_hours"),
        grace_minutes=_int_or_none(event, "grace_minutes"),
        page_size=_int_or_none(event, "page_size") or 100,
        logger=logger,
    )

    duration_ms = int((time.time() - start_time) * 1000)

    metrics.add_metric("FormsScanned", MetricUnit.Count, result.forms_scanned)
    metrics.add_metric("FormsChecked", MetricUnit.Count, result.forms_checked)
    # FormsWithMissingFiles é a métrica do alarme: qualquer valor > 0 significa
    # vistoria concluída com foto que nunca chegou ao S3.
    metrics.add_metric("FormsWithMissingFiles", MetricUnit.Count, result.forms_with_missing_files)
    metrics.add_metric("FilesExpected", MetricUnit.Count, result.files_expected)
    metrics.add_metric("FilesMissing", MetricUnit.Count, result.files_missing)
    metrics.add_metric("FilesUnknown", MetricUnit.Count, result.files_unknown)
    metrics.add_metric("S3ListRequests", MetricUnit.Count, result.list_requests)
    metrics.add_metric("ReconcileDurationMs", MetricUnit.Milliseconds, duration_ms)

    for incomplete in result.incomplete_forms:
        with single_metric(
            name="FilesMissingBySystem",
            unit=MetricUnit.Count,
            value=incomplete["files_missing"],
            namespace=METRICS_NAMESPACE,
            default_dimensions={"service": SERVICE_NAME, "system": incomplete["system"]},
        ):
            # single_metric emite a métrica ao sair do contexto; corpo vazio é intencional.
            pass

    payload = {
        "window_start": result.window_start,
        "window_end": result.window_end,
        "duration_ms": duration_ms,
        "totals": {
            "forms_scanned": result.forms_scanned,
            "forms_checked": result.forms_checked,
            "forms_with_missing_files": result.forms_with_missing_files,
            "files_expected": result.files_expected,
            "files_missing": result.files_missing,
            "files_unknown": result.files_unknown,
            "list_requests": result.list_requests,
            "pages_loaded": result.pages_loaded,
        },
        "incomplete_forms": result.incomplete_forms,
    }

    logger.info("reconcile_form_files completed", extra=payload)

    return LambdaHttpResponse(status_code=200, body=payload).toDict()
