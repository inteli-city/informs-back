import json
import os
import time
import urllib.request
from typing import Dict, Tuple

from src.shared.domain.repositories.origin_repository_interface import IOriginRepository


DEFAULT_URL_TEMPLATE = (
    "https://g1a99674895752e-intelicity.adb.sa-saopaulo-1.oraclecloudapps.com"
    "/ords/{system}/informs/cadastrar_formulario"
)


class OriginRepositoryApex(IOriginRepository):
    def __init__(self):
        self.url_template = os.environ.get("APEX_FORM_REGISTER_URL_TEMPLATE") or DEFAULT_URL_TEMPLATE
        self.api_key = os.environ.get("APEX_FORM_REGISTER_API_KEY")
        self.timeout = int(os.environ.get("SYNC_FORMS_TIMEOUT", "20"))
        self.retries = int(os.environ.get("SYNC_FORMS_RETRIES", "3"))

    def _build_url(self, origin_system: str) -> str:
        return self.url_template.format(system=origin_system)

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post_json(self, url: str, payload: dict, headers: Dict[str, str]) -> Tuple[int, str]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        for key, value in headers.items():
            req.add_header(key, value)

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            status = resp.getcode()
            body = resp.read().decode("utf-8", errors="replace")
        return status, body

    def sync_form(self, origin_system: str, payload: dict) -> Tuple[bool, int, str]:
        url = self._build_url(origin_system)
        headers = self._build_headers()
        last_status = 0
        last_body = ""

        for attempt in range(self.retries):
            try:
                status, body = self._post_json(url, payload, headers)
                last_status, last_body = status, body
                if 200 <= status < 300:
                    return True, status, body
            except Exception as err:
                last_body = str(err)

            if attempt < self.retries - 1:
                time.sleep(2 ** attempt)

        return False, last_status, last_body
