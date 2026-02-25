import time
import json
import hashlib
from uuid import uuid4
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO
from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.entities.sync_state import SyncState
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.origin_repository_interface import IOriginRepository
from src.shared.domain.repositories.sync_error_form_repository_interface import ISyncErrorFormRepository
from src.shared.domain.repositories.sync_state_repository_interface import ISyncStateRepository
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token


@dataclass
class SyncExecutionMetrics:
    system: str
    execution_id: Optional[str] = None
    sent: int = 0
    failed: int = 0
    pages_loaded: int = 0
    forms_loaded: int = 0
    previous_synced_at: Optional[int] = None
    new_synced_at: Optional[int] = None
    sync_started_at: Optional[int] = None
    sync_ended_at: Optional[int] = None
    start_cursor_fingerprint: Optional[str] = None
    end_cursor_fingerprint: Optional[str] = None
    errors: Optional[List[str]] = None


class SyncFormsOriginUsecase:
    JOB_NAME = "sync_forms_origin"

    def __init__(
        self,
        form_repo: IFormRepository,
        origin_repo: IOriginRepository,
        sync_state_repo: ISyncStateRepository,
        sync_error_form_repo: ISyncErrorFormRepository,
    ):
        self.form_repo = form_repo
        self.origin_repo = origin_repo
        self.sync_state_repo = sync_state_repo
        self.sync_error_form_repo = sync_error_form_repo

    @staticmethod
    def _to_json_compatible(value):
        if isinstance(value, Decimal):
            return int(value) if value == value.to_integral_value() else float(value)
        if isinstance(value, dict):
            return {key: SyncFormsOriginUsecase._to_json_compatible(val) for key, val in value.items()}
        if isinstance(value, list):
            return [SyncFormsOriginUsecase._to_json_compatible(item) for item in value]
        return value

    @staticmethod
    def _fingerprint(value) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            raw = value
        else:
            raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    def __call__(
        self,
        systems: List[str],
        system_mapping: Dict[str, str],
        bootstrap_window_minutes: int,
        page_size: int,
        full_sync_on_first_run: bool = False,
        logger=None,
    ) -> List[SyncExecutionMetrics]:
        now_at = int(time.time() * 1000)
        bootstrap_window = bootstrap_window_minutes * 60 * 1000
        fallback_synced_at = now_at - bootstrap_window

        results: List[SyncExecutionMetrics] = []

        for system in systems:
            origin_system = system_mapping.get(system)
            if not origin_system:
                if logger:
                    logger.warning("system mapping not found", extra={"system": system})
                results.append(SyncExecutionMetrics(system=system, sent=0, failed=0, errors=["system mapping not found"]))
                continue

            previous_state = self.sync_state_repo.get_state(self.JOB_NAME, system)
            previous_synced_at = previous_state.checkpoint_synced_at if previous_state is not None else None
            is_first_sync = previous_state is None
            if previous_synced_at is None:
                if full_sync_on_first_run:
                    previous_synced_at = 0
                    sync_started_at = 0
                else:
                    previous_synced_at = fallback_synced_at
                    sync_started_at = max(0, previous_synced_at + 1)
            else:
                sync_started_at = max(0, previous_synced_at + 1)
            sync_ended_at = now_at
            start_key = None
            execution_id = str(uuid4())

            self.sync_state_repo.set_state(
                SyncState(
                    job_name=self.JOB_NAME,
                    system=system,
                    checkpoint_synced_at=previous_synced_at,
                    status="RUNNING",
                    execution_id=execution_id,
                    started_at=now_at,
                    ended_at=None,
                    window_end=sync_ended_at,
                    updated_at=now_at,
                )
            )

            result = SyncExecutionMetrics(
                system=system,
                execution_id=execution_id,
                sent=0,
                failed=0,
                previous_synced_at=previous_synced_at,
                new_synced_at=previous_synced_at,
                sync_started_at=sync_started_at,
                sync_ended_at=sync_ended_at,
                start_cursor_fingerprint=self._fingerprint(start_key),
                errors=[],
            )
            page = 1
            total_loaded = 0
            processed_form_ids = set()

            if logger:
                logger.info(
                    "sync system started",
                    extra={
                        "system": system,
                        "origin_system": origin_system,
                        "page_size": page_size,
                        "previous_synced_at": previous_synced_at,
                        "previous_synced_at_iso": datetime.fromtimestamp(previous_synced_at / 1000, timezone.utc).isoformat(),
                        "sync_started_at": sync_started_at,
                        "sync_ended_at": sync_ended_at,
                        "execution_id": execution_id,
                        "sync_started_at_iso": datetime.fromtimestamp(sync_started_at / 1000, timezone.utc).isoformat(),
                        "sync_ended_at_iso": datetime.fromtimestamp(sync_ended_at / 1000, timezone.utc).isoformat(),
                        "full_sync_on_first_run": full_sync_on_first_run,
                        "is_first_sync": is_first_sync,
                    },
                )

            def process_form(form):
                payload = FormDynamoDTO.from_entity(form).to_dynamo()
                payload["id"] = form.id
                payload = self._to_json_compatible(payload)
                form_id = payload.get("id")

                ok, status, body = self.origin_repo.sync_form(
                    origin_system,
                    payload,
                    execution_id=execution_id,
                    logger=logger,
                )
                if ok:
                    result.sent += 1
                    self.sync_error_form_repo.delete_error_forms(
                        job_name=self.JOB_NAME,
                        system=system,
                        form_ids=[form.id],
                    )
                    if logger:
                        logger.info(
                            "form synced",
                            extra={
                                "system": system,
                                "origin_system": origin_system,
                                "form_id": form_id,
                                "status": status,
                                "execution_id": execution_id,
                            },
                        )
                    return

                result.failed += 1
                snippet = body[:500] if isinstance(body, str) else str(body)
                result.errors.append(f"{form_id} -> {status} {snippet}")
                self.sync_error_form_repo.upsert_error_form(
                    SyncErrorForm(
                        job_name=self.JOB_NAME,
                        system=system,
                        form_id=form.id,
                        source_updated_at=form.updated_at,
                        last_failed_at=int(time.time() * 1000),
                    )
                )
                if logger:
                    logger.warning(
                        "form sync failed",
                        extra={
                            "system": system,
                            "origin_system": origin_system,
                            "form_id": form_id,
                            "status": status,
                            "execution_id": execution_id,
                        },
                    )

            while True:
                if logger:
                    logger.info(
                        "loading forms batch",
                        extra={
                            "system": system,
                            "origin_system": origin_system,
                            "page": page,
                            "has_start_key": start_key is not None,
                            "cursor_in_fingerprint": self._fingerprint(start_key),
                        },
                    )
                batch, next_key = self.form_repo.get_forms_updated_since(
                    system=system,
                    updated_at_start=sync_started_at,
                    updated_at_end=sync_ended_at,
                    limit=page_size,
                    exclusive_start_key=start_key,
                )
                batch_count = len(batch)
                total_loaded += batch_count
                updated_min = min((form.updated_at for form in batch), default=None)
                updated_max = max((form.updated_at for form in batch), default=None)
                first_form_id = batch[0].id if batch else None
                last_form_id = batch[-1].id if batch else None

                if logger:
                    logger.info(
                        "forms batch loaded",
                        extra={
                            "system": system,
                            "origin_system": origin_system,
                            "page": page,
                            "forms_in_batch": batch_count,
                            "has_next_page": next_key is not None,
                            "cursor_out_fingerprint": self._fingerprint(next_key),
                            "batch_updated_at_min": updated_min,
                            "batch_updated_at_max": updated_max,
                            "batch_first_form_id": first_form_id,
                            "batch_last_form_id": last_form_id,
                        },
                    )

                for form in batch:
                    processed_form_ids.add(form.id)
                    process_form(form)

                if not next_key:
                    break

                start_key = try_decode_pagination_token(next_key)
                if start_key is None:
                    result.errors.append("invalid pagination token")
                    if logger:
                        logger.warning(
                            "invalid pagination token",
                            extra={
                                "system": system,
                                "origin_system": origin_system,
                                "next_key_sample": str(next_key)[:200],
                            },
                        )
                    break
                page += 1

            pending_error_forms = self.sync_error_form_repo.list_error_forms(self.JOB_NAME, system)
            for pending_error in pending_error_forms:
                if pending_error.form_id in processed_form_ids:
                    continue
                form = self.form_repo.get_form_by_id(user_id="", form_id=pending_error.form_id)
                if form is None:
                    if logger:
                        logger.warning(
                            "pending sync error form not found",
                            extra={
                                "system": system,
                                "form_id": pending_error.form_id,
                            },
                        )
                    continue
                process_form(form)
                total_loaded += 1

            result.new_synced_at = sync_ended_at
            self.sync_state_repo.set_state(
                SyncState(
                    job_name=self.JOB_NAME,
                    system=system,
                    checkpoint_synced_at=sync_ended_at,
                    status="COMPLETED",
                    execution_id=execution_id,
                    started_at=now_at,
                    ended_at=int(time.time() * 1000),
                    window_end=sync_ended_at,
                    updated_at=int(time.time() * 1000),
                )
            )
            result.pages_loaded = page
            result.forms_loaded = total_loaded
            result.end_cursor_fingerprint = self._fingerprint(next_key)

            if logger:
                logger.info(
                    "sync system completed",
                    extra={
                        "system": system,
                        "origin_system": origin_system,
                        "pages_loaded": page,
                        "forms_loaded": total_loaded,
                        "sent": result.sent,
                        "failed": result.failed,
                        "execution_id": execution_id,
                        "previous_synced_at": result.previous_synced_at,
                        "new_synced_at": result.new_synced_at,
                        "errors_count": len(result.errors),
                    },
                )

            if not result.errors:
                result.errors = None

            results.append(result)

        return results
