import os

import pytest

from src.modules.refresh_presign.app.refresh_presign_usecase import RefreshPresignUsecase
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

os.environ["STAGE"] = "TEST"

FIRST_PATH = "2026/system/form/sections/1/0/aaaa.jpeg"
SECOND_PATH = "2026/system/form/sections/1/0/bbbb.jpeg"


def make_usecase_with_photos():
    form_repo = FormRepositoryMock()
    file_repo = FileRepositoryMock()
    usecase = RefreshPresignUsecase(form_repo, file_repo)

    form = form_repo.forms[0]
    file_field = FileField(
        label='fotos',
        required=False,
        key='FOTOS0',
        order=1,
        file_type=FileType.IMAGE,
        value=[build_s3_url(FIRST_PATH), build_s3_url(SECOND_PATH)],
    )
    form.sections = [Section(section_id=1, fields=[file_field])]

    return usecase, form


class TestRefreshPresignUsecase:

    def setup_method(self):
        self.usecase, self.form = make_usecase_with_photos()
        self.user_id = self.form.user_id

    def test_reassina_a_key_existente_sem_criar_key_nova(self):
        files = self.usecase(
            user_id=self.user_id,
            form_id=self.form.id,
            requested_files=[{"file_url": build_s3_url(SECOND_PATH), "mimetype": "image/jpeg"}],
        )

        assert len(files) == 1
        # A key precisa ser exatamente a que já está gravada no formulário:
        # gerar outra deixaria órfão no bucket e a URL do Dynamo apontaria
        # para um objeto que o app nunca vai enviar.
        assert files[0].file_path == SECOND_PATH
        assert files[0].file_url == build_s3_url(SECOND_PATH)
        assert files[0].pre_signed_url.startswith("https://mock-presigned-url/")

    def test_preserva_a_origem_do_arquivo_na_resposta(self):
        files = self.usecase(
            user_id=self.user_id,
            form_id=self.form.id,
            requested_files=[{"file_url": build_s3_url(SECOND_PATH), "mimetype": "image/jpeg"}],
        )

        assert files[0].section_id == 1
        assert files[0].section_instance == 0
        assert files[0].field_key == "FOTOS0"
        # Segundo arquivo da lista — o app usa o índice para casar com o asset local.
        assert files[0].file_index == 1

    def test_renova_varios_arquivos_na_ordem_pedida(self):
        files = self.usecase(
            user_id=self.user_id,
            form_id=self.form.id,
            requested_files=[
                {"file_url": build_s3_url(SECOND_PATH), "mimetype": "image/jpeg"},
                {"file_url": build_s3_url(FIRST_PATH), "mimetype": "image/jpeg"},
            ],
        )

        assert [file.file_path for file in files] == [SECOND_PATH, FIRST_PATH]

    def test_usa_o_mimetype_informado_pelo_cliente(self):
        files = self.usecase(
            user_id=self.user_id,
            form_id=self.form.id,
            requested_files=[{"file_url": build_s3_url(FIRST_PATH), "mimetype": "image/png"}],
        )

        # A assinatura é específica de Content-Type; quem envia o PUT dita o valor.
        assert files[0].mimetype == "image/png"
        assert "mimetype=image/png" in files[0].pre_signed_url

    def test_recusa_arquivo_que_nao_pertence_ao_formulario(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                user_id=self.user_id,
                form_id=self.form.id,
                requested_files=[
                    {"file_url": build_s3_url("2026/system/outro-form/sections/1/0/cccc.jpeg"), "mimetype": "image/jpeg"}
                ],
            )

    def test_recusa_url_fora_do_bucket_configurado(self):
        self.form.sections[0].fields[0].set_value(["https://atacante.example.com/qualquer.jpeg"])

        with pytest.raises(EntityError):
            self.usecase(
                user_id=self.user_id,
                form_id=self.form.id,
                requested_files=[{"file_url": "https://atacante.example.com/qualquer.jpeg", "mimetype": "image/jpeg"}],
            )

    def test_formulario_inexistente(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                user_id=self.user_id,
                form_id="nao-existe",
                requested_files=[{"file_url": build_s3_url(FIRST_PATH), "mimetype": "image/jpeg"}],
            )

    def test_recusa_requester_que_nao_e_dono_do_formulario(self):
        self.form.user_id = "outro-usuario"

        with pytest.raises((ForbiddenAction, NoItemsFound)):
            self.usecase(
                user_id=self.user_id,
                form_id=self.form.id,
                requested_files=[{"file_url": build_s3_url(FIRST_PATH), "mimetype": "image/jpeg"}],
            )

    def test_renova_mesmo_com_formulario_ja_concluido(self):
        # É o cenário que motiva o endpoint: o /submit não pode ser repetido,
        # mas as fotos que faltaram ainda precisam de URL nova.
        from src.shared.domain.enums.form_status_enum import FormStatus
        self.form.status = FormStatus.COMPLETED

        files = self.usecase(
            user_id=self.user_id,
            form_id=self.form.id,
            requested_files=[{"file_url": build_s3_url(FIRST_PATH), "mimetype": "image/jpeg"}],
        )

        assert files[0].file_path == FIRST_PATH
