import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from src.modules.get_all_forms.app.get_all_forms_viewmodel import FormItemViewmodel
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.origin_repository_interface import IOriginRepository
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token


@dataclass
class SyncResult:
    system: str
    sent: int = 0
    failed: int = 0
    errors: Optional[List[str]] = None


class SyncFormsOriginUsecase:
    def __init__(self, form_repo: IFormRepository, origin_repo: IOriginRepository):
        self.form_repo = form_repo
        self.origin_repo = origin_repo

    def __call__(
        self,
        systems: List[str],
        system_mapping: Dict[str, str],
        window_minutes: int,
        limit: int,
    ) -> List[SyncResult]:
        now_ms = int(time.time() * 1000)
        window_ms = window_minutes * 60 * 1000
        created_at_start = now_ms - window_ms
        created_at_end = now_ms

        results: List[SyncResult] = []

        for system in systems:
            origin_system = system_mapping.get(system)
            if not origin_system:
                results.append(SyncResult(system=system, sent=0, failed=0, errors=["system mapping not found"]))
                continue

            result = SyncResult(system=system, sent=0, failed=0, errors=[])
            start_key = None

            while True:
                batch, next_key = self.form_repo.get_all_forms(
                    limit=limit,
                    exclusive_start_key=start_key,
                    status=None,
                    system=system,
                    user_id=None,
                    created_at_start=created_at_start,
                    created_at_end=created_at_end,
                    search=None,
                )

                for form in batch:
                    payload = FormItemViewmodel(form).to_dict()
                    ok, status, body = self.origin_repo.sync_form(origin_system, payload)
                    if ok:
                        result.sent += 1
                    else:
                        result.failed += 1
                        snippet = body[:500] if isinstance(body, str) else str(body)
                        result.errors.append(f"{payload.get('id')} -> {status} {snippet}")

                if not next_key:
                    break

                start_key = try_decode_pagination_token(next_key)
                if start_key is None:
                    result.errors.append("invalid pagination token")
                    break

            if not result.errors:
                result.errors = None

            results.append(result)

        return results
