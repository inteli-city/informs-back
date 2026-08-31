from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import ErrorWithFile
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token
from src.shared.helpers.functions.s3_url import extract_file_path


@dataclass
class FormReconciliation:
    """O que um formulário prometeu e o que o S3 realmente tem."""
    form_id: str
    system: str
    status: str
    files_expected: int = 0
    files_missing: int = 0
    files_invalid: int = 0
    files_unknown: int = 0
    missing_sample: List[dict] = field(default_factory=list)
    invalid_sample: List[dict] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return self.files_missing == 0 and self.files_invalid == 0 and self.files_unknown == 0


@dataclass
class ReconcileResult:
    forms_scanned: int = 0
    forms_checked: int = 0
    forms_with_missing_files: int = 0
    files_expected: int = 0
    files_missing: int = 0
    files_invalid: int = 0
    files_unknown: int = 0
    list_requests: int = 0
    head_requests: int = 0
    pages_loaded: int = 0
    window_start: Optional[int] = None
    window_end: Optional[int] = None
    incomplete_forms: List[dict] = field(default_factory=list)


class ReconcileFormFilesUsecase:
    """
    Compara as URLs que o formulário afirma ter com as keys que existem no S3.

    Existe porque o upload é feito pelo app direto no S3 (ADR-0005): o backend
    grava a URL final no submit e nunca descobre se o PUT aconteceu. Sem este
    job, foto perdida só aparece quando alguém abre a vistoria meses depois.

    Não escreve nada — apenas relata. O objetivo é a métrica e o alarme avisarem
    no mesmo dia; corrigir o dado é decisão de quem opera.
    """

    RECONCILED_STATUSES = (FormStatus.COMPLETED, FormStatus.SENT)
    # Formulário recém-concluído pode ter upload em andamento. Sem esta carência
    # o job acusaria falta de arquivo que está no meio do caminho.
    DEFAULT_GRACE_MINUTES = 30
    DEFAULT_WINDOW_HOURS = 24
    MAX_MISSING_SAMPLE = 5
    MAX_INCOMPLETE_FORMS_REPORTED = 50

    def __init__(self, form_repo: IFormRepository, file_repo: IFileRepository):
        self.form_repo = form_repo
        self.file_repo = file_repo

    def __call__(
        self,
        systems: Sequence[str],
        updated_at_start: Optional[int] = None,
        updated_at_end: Optional[int] = None,
        window_hours: Optional[int] = None,
        grace_minutes: Optional[int] = None,
        page_size: int = 100,
        logger=None,
    ) -> ReconcileResult:
        now = now_timestamp_ms()
        window_start, window_end = self._resolve_window(updated_at_start, updated_at_end, window_hours, now)
        grace_cutoff = now - self._minutes_to_ms(
            grace_minutes if grace_minutes is not None else self.DEFAULT_GRACE_MINUTES
        )

        result = ReconcileResult(window_start=window_start, window_end=window_end)

        for form in self._iter_forms(systems, window_start, window_end, page_size, result):
            result.forms_scanned += 1
            if form.updated_at is not None and form.updated_at > grace_cutoff:
                continue

            reconciliation = self._reconcile_form(form, result)
            if reconciliation is None:
                continue

            result.forms_checked += 1
            self._accumulate(result, reconciliation, logger)

        self._log_summary(result, grace_cutoff, logger)
        return result

    def _resolve_window(
        self,
        updated_at_start: Optional[int],
        updated_at_end: Optional[int],
        window_hours: Optional[int],
        now: int,
    ) -> Tuple[int, int]:
        end = updated_at_end if updated_at_end is not None else now
        if updated_at_start is not None:
            return updated_at_start, end
        hours = window_hours if window_hours is not None else self.DEFAULT_WINDOW_HOURS
        return end - hours * 60 * 60 * 1000, end

    @staticmethod
    def _minutes_to_ms(minutes: int) -> int:
        return minutes * 60 * 1000

    def _iter_forms(
        self,
        systems: Sequence[str],
        window_start: int,
        window_end: int,
        page_size: int,
        result: ReconcileResult,
    ):
        # O GSI2 é particionado por sistema. Por isso cada sistema é configurado
        # explicitamente por ambiente: não há Scan da single-table para descobrir
        # formulários ou partições.
        for system in systems:
            exclusive_start_key = None
            while True:
                forms, next_key = self.form_repo.get_forms_updated_since(
                    system=system,
                    updated_at_start=window_start,
                    updated_at_end=window_end,
                    limit=page_size,
                    exclusive_start_key=exclusive_start_key,
                    status=list(self.RECONCILED_STATUSES),
                )
                result.pages_loaded += 1
                for form in forms:
                    yield form

                if not next_key:
                    break
                # O repositório devolve token opaco; o Dynamo recebe a chave
                # crua na próxima Query do mesmo sistema.
                exclusive_start_key = try_decode_pagination_token(next_key)
                if exclusive_start_key is None:
                    break

    def _reconcile_form(self, form: Form, result: ReconcileResult) -> Optional[FormReconciliation]:
        stored_files = form.stored_files()
        if not stored_files:
            return None

        paths_by_url: Dict[str, Optional[str]] = {
            stored.file_url: extract_file_path(stored.file_url) for stored in stored_files
        }
        known_paths = {path for path in paths_by_url.values() if path}
        existing = self._existing_paths(known_paths, result)

        reconciliation = FormReconciliation(
            form_id=form.id,
            system=form.system,
            status=form.status.value,
            files_expected=len(stored_files),
        )

        for stored in stored_files:
            file_path = paths_by_url.get(stored.file_url)
            if file_path is None:
                # URL fora do bucket configurado: nao e dado que este job saiba julgar.
                reconciliation.files_unknown += 1
                continue
            if file_path not in existing:
                reconciliation.files_missing += 1
                if len(reconciliation.missing_sample) < self.MAX_MISSING_SAMPLE:
                    reconciliation.missing_sample.append(stored.to_dict())
                continue
            if self._has_integrity_expectation(stored):
                result.head_requests += 1
                try:
                    actual = self.file_repo.get_file_metadata(file_path)
                except ErrorWithFile as err:
                    # HeadObject falhando (arquivo apagado entre o LIST e aqui, S3
                    # com erro passageiro) não pode derrubar a execução inteira —
                    # isso silenciaria o heartbeat do Kuma e pularia todo o resto
                    # do lote/sistema. Degrada como "unknown", mesmo tratamento já
                    # dado à URL fora do bucket configurado.
                    reconciliation.files_unknown += 1
                    if len(reconciliation.invalid_sample) < self.MAX_MISSING_SAMPLE:
                        reconciliation.invalid_sample.append({"expected": stored.to_dict(), "error": err.message})
                    continue
                if not self._matches_integrity(stored, actual):
                    reconciliation.files_invalid += 1
                    if len(reconciliation.invalid_sample) < self.MAX_MISSING_SAMPLE:
                        reconciliation.invalid_sample.append({"expected": stored.to_dict(), "actual": actual})

        return reconciliation

    @staticmethod
    def _has_integrity_expectation(stored) -> bool:
        # Só o checksum é sinal de integridade que vale um HEAD: mimetype é
        # declarado pelo próprio cliente (nunca verificado), e size sozinho não
        # pega corrupção de conteúdo. Gatilhar em qualquer um dos três reverteria
        # a otimização de "1 LIST resolve o formulário" de volta para 1 HEAD por
        # arquivo, já que mimetype está presente em praticamente todo upload.
        return stored.checksum_sha256 is not None

    @staticmethod
    def _matches_integrity(stored, actual: dict) -> bool:
        return (
            (stored.mimetype is None or actual.get("mimetype") == stored.mimetype)
            and (stored.size_bytes is None or actual.get("size_bytes") == stored.size_bytes)
            and (stored.checksum_sha256 is None or actual.get("checksum_sha256") == stored.checksum_sha256)
        )

    def _existing_paths(self, file_paths: Set[str], result: ReconcileResult) -> Set[str]:
        existing: Set[str] = set()
        for prefix in self._prefixes_of(file_paths):
            existing |= self.file_repo.list_file_paths(prefix)
            result.list_requests += 1
        return existing

    @staticmethod
    def _prefixes_of(file_paths: Set[str]) -> Set[str]:
        """
        Um LIST por raiz de formulário ({ano}/{sistema}/{form_id}/) em vez de um
        HEAD por arquivo. O ano vem da key, não do created_at: formulário criado
        em dezembro e submetido em janeiro grava no ano do submit.
        """
        prefixes = set()
        for file_path in file_paths:
            segments = file_path.split("/")
            if len(segments) >= 4:
                prefixes.add("/".join(segments[:3]) + "/")
        return prefixes

    def _accumulate(self, result: ReconcileResult, reconciliation: FormReconciliation, logger) -> None:
        result.files_expected += reconciliation.files_expected
        result.files_missing += reconciliation.files_missing
        result.files_invalid += reconciliation.files_invalid
        result.files_unknown += reconciliation.files_unknown

        if reconciliation.is_complete:
            return

        result.forms_with_missing_files += 1
        if len(result.incomplete_forms) < self.MAX_INCOMPLETE_FORMS_REPORTED:
            result.incomplete_forms.append(self._describe(reconciliation))

        if logger:
            logger.warning("form with missing files", extra=self._describe(reconciliation))

    @staticmethod
    def _describe(reconciliation: FormReconciliation) -> dict:
        return {
            "form_id": reconciliation.form_id,
            "system": reconciliation.system,
            "status": reconciliation.status,
            "files_expected": reconciliation.files_expected,
            "files_missing": reconciliation.files_missing,
            "files_invalid": reconciliation.files_invalid,
            "files_unknown": reconciliation.files_unknown,
            "missing_sample": reconciliation.missing_sample,
            "invalid_sample": reconciliation.invalid_sample,
        }

    @staticmethod
    def _log_summary(result: ReconcileResult, grace_cutoff: int, logger) -> None:
        if not logger:
            return
        logger.info(
            "reconcile_form_files summary",
            extra={
                "window_start": result.window_start,
                "window_end": result.window_end,
                "grace_cutoff": grace_cutoff,
                "forms_scanned": result.forms_scanned,
                "forms_checked": result.forms_checked,
                "forms_with_missing_files": result.forms_with_missing_files,
                "files_expected": result.files_expected,
                "files_missing": result.files_missing,
                "files_invalid": result.files_invalid,
                "files_unknown": result.files_unknown,
                "list_requests": result.list_requests,
                "head_requests": result.head_requests,
                "pages_loaded": result.pages_loaded,
            },
        )
