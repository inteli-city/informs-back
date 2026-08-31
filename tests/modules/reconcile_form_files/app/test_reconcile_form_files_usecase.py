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
        usecase = ReconcileFormFilesUsecase(self.form_repo, self.file_repo)
        self.usecase = lambda **kwargs: usecase(systems=("GAIA",), **kwargs)
        self.now = now_timestamp_ms()

        # Só o formulário preparado em cada teste deve entrar na janela.
        for form in self.form_repo.forms:
            form.status = FormStatus.PENDING

        self.form = self.form_repo.forms[0]

    def _prepare_form(self, paths, status=FormStatus.COMPLETED, updated_at=None, file_integrity=None):
        urls = [build_s3_url(path) for path in paths]
        self.form.status = status
        self.form.created_at = self.now - ONE_HOUR_MS
        self.form.updated_at = updated_at if updated_at is not None else self.now - ONE_HOUR_MS
        self.form.justification = None
        self.form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=urls, file_integrity=file_integrity,
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
        assert self.file_repo.head_calls == []

    def test_mimetype_e_size_sozinhos_nao_disparam_head(self):
        # mimetype é declarado pelo cliente (nunca verificado) e size sozinho
        # não pega corrupção — gatilhar HEAD nesses dois reverteria a otimização
        # de 1 LIST por formulário para 1 HEAD por arquivo, já que praticamente
        # todo upload novo tem mimetype/size preenchidos.
        path = self._paths(1)[0]
        self._prepare_form(
            [path],
            file_integrity=[{"mimetype": "image/jpeg", "size_bytes": 42, "checksum_sha256": None}],
        )
        self.file_repo.existing_file_paths = {path}

        result = self.usecase()

        assert self.file_repo.head_calls == []
        assert result.files_invalid == 0
        assert result.forms_with_missing_files == 0

    def test_valida_tamanho_mime_e_checksum_dos_arquivos_novos(self):
        path = self._paths(1)[0]
        checksum = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        self._prepare_form(
            [path],
            file_integrity=[{
                "mimetype": "image/jpeg",
                "size_bytes": 42,
                "checksum_sha256": checksum,
            }],
        )
        self.file_repo.existing_file_paths = {path}
        self.file_repo.file_metadata[path] = {
            "mimetype": "image/jpeg",
            "size_bytes": 42,
            "checksum_sha256": checksum,
        }

        result = self.usecase()

        assert result.files_invalid == 0
        assert result.forms_with_missing_files == 0
        assert self.file_repo.head_calls == [path]

    def test_acusa_objeto_existente_com_integridade_divergente(self):
        path = self._paths(1)[0]
        self._prepare_form(
            [path],
            file_integrity=[{
                "mimetype": "image/jpeg",
                "size_bytes": 42,
                "checksum_sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
            }],
        )
        self.file_repo.existing_file_paths = {path}
        self.file_repo.file_metadata[path] = {
            "mimetype": "text/xml",
            "size_bytes": 12,
            "checksum_sha256": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=",
        }

        result = self.usecase()

        assert result.files_missing == 0
        assert result.files_invalid == 1
        assert result.forms_with_missing_files == 1
        assert result.incomplete_forms[0]["invalid_sample"][0]["actual"]["mimetype"] == "text/xml"

    def test_falha_no_head_de_um_arquivo_nao_derruba_a_execucao(self):
        # Regressão: um HeadObject falhando (arquivo removido entre o LIST e o
        # HEAD, erro passageiro do S3) não pode propagar e abortar o job inteiro
        # — isso silenciaria o heartbeat do Kuma e pularia o resto do lote.
        checksum_a = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        checksum_b = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
        paths = self._paths(2)
        self._prepare_form(
            paths,
            file_integrity=[
                {"mimetype": "image/jpeg", "size_bytes": 1, "checksum_sha256": checksum_a},
                {"mimetype": "image/jpeg", "size_bytes": 2, "checksum_sha256": checksum_b},
            ],
        )
        self.file_repo.existing_file_paths = set(paths)
        self.file_repo.file_metadata[paths[1]] = {"mimetype": "image/jpeg", "size_bytes": 2, "checksum_sha256": checksum_b}
        self.file_repo.raise_on_head = {paths[0]}

        result = self.usecase()

        assert result.forms_checked == 1
        assert result.files_missing == 0
        assert result.files_unknown == 1
        assert result.files_invalid == 0
        assert result.forms_with_missing_files == 1
        assert self.file_repo.head_calls == paths

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
        # updated_at, não created_at, é o que define a janela — um formulário
        # criado há muito tempo mas concluído agora ainda deve ser pego (ver
        # test_backfill_com_janela_explicita_alcanca_o_historico e o caso real
        # OS-6179, criado dias antes de ser submetido).
        self._prepare_form(paths, updated_at=self.now - 90 * 24 * ONE_HOUR_MS)
        self.file_repo.existing_file_paths = set()

        result = self.usecase(window_hours=24)

        assert result.forms_scanned == 0

    def test_backfill_com_janela_explicita_alcanca_o_historico(self):
        paths = self._paths(2)
        self._prepare_form(paths, updated_at=self.now - 90 * 24 * ONE_HOUR_MS)
        self.file_repo.existing_file_paths = set()

        result = self.usecase(updated_at_start=0, updated_at_end=self.now)

        assert result.forms_checked == 1
        assert result.files_missing == 2

    def test_pagina_corretamente_com_mais_de_uma_pagina(self):
        # Regressão: _iter_forms repassava o token de paginação (string opaca
        # devolvida por get_all_forms) direto como exclusive_start_key sem
        # decodificar — a segunda página quebrava com AttributeError.
        paths_a = self._paths(1)
        self._prepare_form(paths_a)

        second_form = self.form_repo.forms[1]
        second_form.status = FormStatus.COMPLETED
        second_form.created_at = self.now - ONE_HOUR_MS
        second_form.updated_at = self.now - ONE_HOUR_MS
        second_form.justification = None
        paths_b = self._paths(1, form_id=second_form.id)
        second_form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=[build_s3_url(p) for p in paths_b],
            )])
        ]

        self.file_repo.existing_file_paths = set(paths_a) | set(paths_b)

        result = self.usecase(page_size=1)

        assert result.forms_scanned == 2
        assert result.forms_checked == 2
        assert result.pages_loaded >= 2

    def test_consulta_gsi_por_cada_sistema_sem_usar_listagem_global(self, monkeypatch):
        paths_a = self._paths(1, system="GAIA")
        self._prepare_form(paths_a)

        second_form = self.form_repo.forms[1]
        second_form.system = "SGC"
        second_form.status = FormStatus.SENT
        second_form.created_at = self.now - ONE_HOUR_MS
        second_form.updated_at = self.now - ONE_HOUR_MS
        second_form.justification = None
        paths_b = self._paths(1, form_id=second_form.id, system="SGC")
        second_form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=[build_s3_url(paths_b[0])],
            )])
        ]
        self.file_repo.existing_file_paths = set(paths_a) | set(paths_b)

        def global_listing_must_not_run(*args, **kwargs):
            raise AssertionError("a reconciliação não pode chamar get_all_forms/Scan")

        monkeypatch.setattr(self.form_repo, "get_all_forms", global_listing_must_not_run)
        result = ReconcileFormFilesUsecase(self.form_repo, self.file_repo)(
            systems=("GAIA", "SGC"),
        )

        assert result.forms_scanned == 2
        assert result.forms_checked == 2
        assert result.pages_loaded == 2

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
