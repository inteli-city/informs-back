import os

from src.modules.reconcile_form_files.app.reconcile_form_files_usecase import ReconcileFormFilesUsecase
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

os.environ["STAGE"] = "TEST"

ONE_HOUR_MS = 60 * 60 * 1000


class TestReconcileFormFilesUsecase:

    def setup_method(self):
        self.form_repo = FormRepositoryMock()
        self.file_repo = FileRepositoryMock()
        self.usecase = ReconcileFormFilesUsecase(self.form_repo, self.file_repo)
        self.now = now_timestamp_ms()

        # Só o formulário preparado em cada teste deve entrar na janela.
        for form in self.form_repo.forms:
            form.status = FormStatus.PENDING

        self.form = self.form_repo.forms[0]

    def _prepare_form(self, paths, status=FormStatus.COMPLETED, updated_at=None):
        urls = [build_s3_url(path) for path in paths]
        self.form.status = status
        self.form.created_at = self.now - ONE_HOUR_MS
        self.form.updated_at = updated_at if updated_at is not None else self.now - ONE_HOUR_MS
        self.form.justification = None
        self.form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=urls,
            )])
        ]
        return urls

    def _paths(self, count, form_id=None, year="2026", system="GAIA"):
        form_id = form_id or self.form.id
        return [f"{year}/{system}/{form_id}/sections/1/0/foto{index}.jpeg" for index in range(count)]

    def test_nao_acusa_nada_quando_todos_os_arquivos_estao_no_s3(self):
        paths = self._paths(3)
        self._prepare_form(paths)
        self.file_repo.existing_file_paths = set(paths)

        result = self.usecase()

        assert result.forms_checked == 1
        assert result.files_expected == 3
        assert result.files_missing == 0
        assert result.forms_with_missing_files == 0
        assert result.incomplete_forms == []

    def test_conta_arquivos_ausentes_no_s3(self):
        paths = self._paths(5)
        self._prepare_form(paths)
        # Só os dois primeiros chegaram — o padrão de prefixo do incidente real.
        self.file_repo.existing_file_paths = set(paths[:2])

        result = self.usecase()

        assert result.files_expected == 5
        assert result.files_missing == 3
        assert result.forms_with_missing_files == 1
        assert result.incomplete_forms[0]["form_id"] == self.form.id
        assert result.incomplete_forms[0]["files_missing"] == 3

    def test_usa_um_list_por_formulario_e_nao_um_head_por_arquivo(self):
        paths = self._paths(38)
        self._prepare_form(paths)
        self.file_repo.existing_file_paths = set(paths)

        result = self.usecase()

        assert result.list_requests == 1
        assert self.file_repo.list_calls == [f"2026/GAIA/{self.form.id}/"]

    def test_respeita_a_carencia_de_formulario_recem_concluido(self):
        paths = self._paths(3)
        # Concluído há 1 minuto: upload pode estar em andamento.
        self._prepare_form(paths, updated_at=self.now - 60 * 1000)
        self.file_repo.existing_file_paths = set()

        result = self.usecase()

        assert result.forms_scanned == 1
        assert result.forms_checked == 0
        assert result.files_missing == 0

    def test_carencia_configuravel_permite_checar_imediatamente(self):
        paths = self._paths(3)
        self._prepare_form(paths, updated_at=self.now - 60 * 1000)
        self.file_repo.existing_file_paths = set()

        result = self.usecase(grace_minutes=0)

        assert result.forms_checked == 1
        assert result.files_missing == 3

    def test_ignora_formulario_sem_arquivo(self):
        self._prepare_form([])
        self.form.sections = []

        result = self.usecase()

        assert result.forms_checked == 0
        assert result.list_requests == 0

    def test_conta_como_desconhecida_a_url_fora_do_bucket(self):
        self._prepare_form([])
        self.form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=["https://outro-host.example.com/foto.jpeg"],
            )])
        ]

        result = self.usecase()

        assert result.files_unknown == 1
        assert result.files_missing == 0
        # Ainda entra no relatório: URL que o job não sabe julgar é sinal, não silêncio.
        assert result.forms_with_missing_files == 1

    def test_reconcilia_tambem_formulario_ja_enviado_ao_sistema_de_origem(self):
        paths = self._paths(2)
        self._prepare_form(paths, status=FormStatus.SENT)
        self.file_repo.existing_file_paths = set()

        result = self.usecase()

        assert result.forms_checked == 1
        assert result.incomplete_forms[0]["status"] == "SENT"

    def test_ignora_formulario_fora_da_janela(self):
        paths = self._paths(2)
        self._prepare_form(paths)
        self.form.created_at = self.now - 90 * 24 * ONE_HOUR_MS
        self.file_repo.existing_file_paths = set()

        result = self.usecase(window_hours=24)

        assert result.forms_scanned == 0

    def test_backfill_com_janela_explicita_alcanca_o_historico(self):
        paths = self._paths(2)
        self._prepare_form(paths)
        self.form.created_at = self.now - 90 * 24 * ONE_HOUR_MS
        self.file_repo.existing_file_paths = set()

        result = self.usecase(created_at_start=0, created_at_end=self.now)

        assert result.forms_checked == 1
        assert result.files_missing == 2

    def test_deriva_o_prefixo_do_ano_gravado_na_key(self):
        # Formulário criado em dezembro e submetido em janeiro grava no ano do
        # submit; derivar o prefixo do created_at olharia para o ano errado.
        paths = self._paths(2, year="2027")
        self._prepare_form(paths)
        self.file_repo.existing_file_paths = set(paths)

        result = self.usecase()

        assert self.file_repo.list_calls == [f"2027/GAIA/{self.form.id}/"]
        assert result.files_missing == 0

    def test_inclui_a_imagem_da_justificativa_na_conferencia(self):
        photo_paths = self._paths(1)
        self._prepare_form(photo_paths)
        justification_path = f"2026/GAIA/{self.form.id}/justification/abc.jpeg"

        from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
        self.form.justification = Justification(
            options=[JustificationOption(option='option', required_image=True, required_text=True)],
            selected=SelectedJustification(
                option='option', text='t', image_url=build_s3_url(justification_path)
            ),
        )
        self.file_repo.existing_file_paths = set(photo_paths)

        result = self.usecase()

        assert result.files_expected == 2
        assert result.files_missing == 1

    def test_amostra_de_ausentes_e_limitada(self):
        paths = self._paths(20)
        self._prepare_form(paths)
        self.file_repo.existing_file_paths = set()

        result = self.usecase()

        assert result.files_missing == 20
        assert len(result.incomplete_forms[0]["missing_sample"]) == ReconcileFormFilesUsecase.MAX_MISSING_SAMPLE

    def test_amostra_de_ausentes_aponta_a_origem_do_arquivo(self):
        paths = self._paths(2)
        self._prepare_form(paths)
        self.file_repo.existing_file_paths = set()

        result = self.usecase()

        sample = result.incomplete_forms[0]["missing_sample"][0]
        assert sample["field_key"] == "FOTOS0"
        assert sample["section_id"] == 1
        assert sample["section_instance"] == 0
