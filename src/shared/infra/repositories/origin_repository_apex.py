import json
import os
import time
import urllib.request
from typing import Dict, Optional, Tuple

from src.shared.domain.repositories.origin_repository_interface import IOriginRepository


DEFAULT_URL_TEMPLATE = (
    "https://g1a99674895752e-intelicity.adb.sa-saopaulo-1.oraclecloudapps.com"
    "/ords/{system}/informs/cadastrar_formulario"
)


class OriginRepositoryApex(IOriginRepository):
    def __init__(self):
        self.url_template = os.environ.get("APEX_FORM_REGISTER_URL_TEMPLATE") or DEFAULT_URL_TEMPLATE
        self.timeout = int(os.environ.get("SYNC_FORMS_TIMEOUT", "20"))
        self.retries = int(os.environ.get("SYNC_FORMS_RETRIES", "3"))

    def _build_url(self, origin_system: str) -> str:
        return self.url_template.format(system=origin_system)

    def _build_headers(self, execution_id: Optional[str] = None) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if execution_id:
            headers["X-Informs-Execution-Id"] = execution_id
        return headers

    def _post_json(self, url: str, payloads: list[dict], headers: Dict[str, str]) -> Tuple[int, str]:
        data = json.dumps({"forms": payloads}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        for key, value in headers.items():
            req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
        return status, body

    def sync_forms(
        self,
        origin_system: str,
        payloads: list[dict],
        execution_id: Optional[str] = None,
        logger: Optional[object] = None,
    ) -> Tuple[bool, int, str]:
        if not payloads:
            return True, 200, "EMPTY_BATCH"

        url = self._build_url(origin_system)
        headers = self._build_headers(execution_id=execution_id)
        last_status = 0
        last_body = ""
        form_ids = [item.get("id") for item in payloads if isinstance(item, dict)]
        first_form_id = form_ids[0] if form_ids else None
        last_form_id = form_ids[-1] if form_ids else None

        for attempt in range(self.retries):
            if logger:
                logger.info(
                    "origin request attempt",
                    extra={
                        "origin_system": origin_system,
                        "batch_size": len(payloads),
                        "batch_first_form_id": first_form_id,
                        "batch_last_form_id": last_form_id,
                        "attempt": attempt + 1,
                        "max_retries": self.retries,
                        "url": url,
                        "execution_id": execution_id,
                    },
                )
            try:
                status, body = self._post_json(url, payloads, headers)
                last_status, last_body = status, body
                if 200 <= status < 300:
                    if logger:
                        logger.info(
                            "origin request success",
                            extra={
                                "origin_system": origin_system,
                                "batch_size": len(payloads),
                                "batch_first_form_id": first_form_id,
                                "batch_last_form_id": last_form_id,
                                "status": status,
                                "execution_id": execution_id,
                            },
                        )
                    return True, status, body
                if logger:
                    logger.warning(
                        "origin request non-2xx",
                        extra={
                            "origin_system": origin_system,
                            "batch_size": len(payloads),
                            "batch_first_form_id": first_form_id,
                            "batch_last_form_id": last_form_id,
                            "status": status,
                            "execution_id": execution_id,
                            "response_body_sample": body[:500] if isinstance(body, str) else str(body),
                        },
                    )
            except Exception as err:
                last_body = str(err)
                if logger:
                    logger.warning(
                        "origin request exception",
                        extra={
                            "origin_system": origin_system,
                            "batch_size": len(payloads),
                            "batch_first_form_id": first_form_id,
                            "batch_last_form_id": last_form_id,
                            "attempt": attempt + 1,
                            "execution_id": execution_id,
                            "error": last_body,
                        },
                    )

            if attempt < self.retries - 1:
                time.sleep(2 ** attempt)

        return False, last_status, last_body
