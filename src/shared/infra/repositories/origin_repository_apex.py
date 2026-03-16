import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple

from src.shared.domain.repositories.origin_repository_interface import IOriginRepository


DEFAULT_URL_TEMPLATE = (
    "https://g1a99674895752e-intelicity.adb.sa-saopaulo-1.oraclecloudapps.com"
    "/ords/{system}/informs/cadastrar_formulario"
)
GAIA_URL_TEMPLATE = (
    "https://g1a99674895752e-intelicitydataapex.adb.sa-saopaulo-1.oraclecloudapps.com"
    "/ords/{system}/informs/cadastrar_formulario"
)


class OriginRepositoryApex(IOriginRepository):
    SUCCESS_STATUS_CODE = 200
    EXPECTED_STATUS_CODES = {
        200,
        202,
        204,
        400,
        401,
        403,
        404,
        408,
        409,
        413,
        415,
        422,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(self):
        self.url_template = DEFAULT_URL_TEMPLATE
        self.gaia_url_template = GAIA_URL_TEMPLATE
        self.timeout = int(os.environ.get("SYNC_FORMS_TIMEOUT", "20"))

    def _build_url(self, origin_system: str) -> str:
        normalized_system = (origin_system or "").strip().lower()
        template = self.gaia_url_template if normalized_system == "gaia" else self.url_template
        return template.format(system=origin_system)

    def _post_json(
        self,
        url: str,
        payloads: list[dict],
        execution_id: Optional[str] = None,
    ) -> Tuple[int, str]:
        body = {"forms": payloads}
        if execution_id:
            body["execution_id"] = execution_id
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
        return status, body

    def _get_batch_info(self, payloads: list[dict]) -> Tuple[Optional[str], Optional[str]]:
        form_ids = [item.get("id") for item in payloads if isinstance(item, dict)]
        first_form_id = form_ids[0] if form_ids else None
        last_form_id = form_ids[-1] if form_ids else None
        return first_form_id, last_form_id

    def _log_request_started(
        self,
        logger,
        origin_system: str,
        payloads: list[dict],
        first_form_id: Optional[str],
        last_form_id: Optional[str],
        url: str,
        execution_id: Optional[str],
    ) -> None:
        logger.info(
            "origin request started",
            extra={
                "origin_system": origin_system,
                "batch_size": len(payloads),
                "batch_first_form_id": first_form_id,
                "batch_last_form_id": last_form_id,
                "url": url,
                "timeout_seconds": self.timeout,
                "execution_id": execution_id,
            },
        )

    def _log_request_completed(
        self,
        logger,
        origin_system: str,
        payloads: list[dict],
        first_form_id: Optional[str],
        last_form_id: Optional[str],
        status: int,
        body: str,
        duration_ms: int,
        execution_id: Optional[str],
    ) -> None:
        log_method = logger.info if status == self.SUCCESS_STATUS_CODE else logger.warning
        log_method(
            "origin request completed",
            extra={
                "origin_system": origin_system,
                "batch_size": len(payloads),
                "batch_first_form_id": first_form_id,
                "batch_last_form_id": last_form_id,
                "status": status,
                "expected_status": status in self.EXPECTED_STATUS_CODES,
                "success": status == self.SUCCESS_STATUS_CODE,
                "duration_ms": duration_ms,
                "execution_id": execution_id,
                "response_body_sample": body[:500] if isinstance(body, str) else str(body),
            },
        )

    def _log_request_exception(
        self,
        logger,
        origin_system: str,
        payloads: list[dict],
        first_form_id: Optional[str],
        last_form_id: Optional[str],
        error: str,
        duration_ms: int,
        execution_id: Optional[str],
    ) -> None:
        logger.error(
            "origin request exception",
            extra={
                "origin_system": origin_system,
                "batch_size": len(payloads),
                "batch_first_form_id": first_form_id,
                "batch_last_form_id": last_form_id,
                "duration_ms": duration_ms,
                "execution_id": execution_id,
                "error": error,
            },
        )

    @staticmethod
    def _safe_http_error_body(err: urllib.error.HTTPError) -> str:
        try:
            if err.fp is None:
                return str(err)
            raw = err.fp.read()
            if isinstance(raw, bytes):
                return raw.decode("utf-8", errors="replace")
            return str(raw)
        except Exception:
            return str(err)

    def sync_forms(
        self,
        origin_system: str,
        payloads: list[dict],
        execution_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> Tuple[bool, int, str]:
        if not payloads:
            return True, self.SUCCESS_STATUS_CODE, "EMPTY_BATCH"

        url = self._build_url(origin_system)
        first_form_id, last_form_id = self._get_batch_info(payloads)
        started_at = time.time()

        if logger:
            self._log_request_started(
                logger=logger,
                origin_system=origin_system,
                payloads=payloads,
                first_form_id=first_form_id,
                last_form_id=last_form_id,
                url=url,
                execution_id=execution_id,
            )

        try:
            status, body = self._post_json(url, payloads, execution_id=execution_id)
        except urllib.error.HTTPError as err:
            status = int(err.code or 0)
            body = self._safe_http_error_body(err)
            duration_ms = int((time.time() - started_at) * 1000)
            if logger:
                self._log_request_completed(
                    logger=logger,
                    origin_system=origin_system,
                    payloads=payloads,
                    first_form_id=first_form_id,
                    last_form_id=last_form_id,
                    status=status,
                    body=body,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
            return False, status, body
        except Exception as err:
            duration_ms = int((time.time() - started_at) * 1000)
            error_msg = str(err)
            if logger:
                self._log_request_exception(
                    logger=logger,
                    origin_system=origin_system,
                    payloads=payloads,
                    first_form_id=first_form_id,
                    last_form_id=last_form_id,
                    error=error_msg,
                    duration_ms=duration_ms,
                    execution_id=execution_id,
                )
            return False, 0, error_msg

        duration_ms = int((time.time() - started_at) * 1000)
        if logger:
            self._log_request_completed(
                logger=logger,
                origin_system=origin_system,
                payloads=payloads,
                first_form_id=first_form_id,
                last_form_id=last_form_id,
                status=status,
                body=body,
                duration_ms=duration_ms,
                execution_id=execution_id,
            )

        if status == self.SUCCESS_STATUS_CODE:
            return True, status, body
        return False, status, body
