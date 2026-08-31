import os

import pytest

from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.stored_file import StoredFile
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

os.environ["STAGE"] = "TEST"


class TestStoredFile:

    def test_exige_url_nao_vazia(self):
        with pytest.raises(EntityError):
            StoredFile(file_url="")

    def test_recusa_section_instance_negativa(self):
        with pytest.raises(EntityError):
            StoredFile(file_url="https://bucket/key.jpeg", section_instance=-1)

    def test_recusa_bool_como_section_id(self):
        with pytest.raises(EntityError):
            StoredFile(file_url="https://bucket/key.jpeg", section_id=True)

    def test_recusa_checksum_com_tamanho_invalido(self):
        # Mesma regra de FileUploadBase (base64 de 32 bytes) — antes StoredFile
        # só checava isinstance(str), então um checksum corrompido chegava
        # inteiro até a comparação de integridade da reconciliação.
        with pytest.raises(EntityError):
            StoredFile(file_url="https://bucket/key.jpeg", checksum_sha256="nao-eh-base64-de-32-bytes")

    def test_aceita_checksum_valido(self):
        checksum = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        stored = StoredFile(file_url="https://bucket/key.jpeg", checksum_sha256=checksum)

        assert stored.checksum_sha256 == checksum


class TestFormStoredFiles:

    def setup_method(self):
        self.form = FormRepositoryMock().forms[0]

    def _with_file_field(self, value, key='FOTOS0', section_id=1, section_instance=0):
        field = FileField(
            label='fotos', required=False, key=key, order=1,
            file_type=FileType.IMAGE, value=value,
        )
        self.form.sections = [
            Section(section_id=section_id, fields=[field], section_instance=section_instance)
        ]
        return field

    def test_enumera_urls_de_lista_com_indice(self):
        self._with_file_field(["https://bucket/a.jpeg", "https://bucket/b.jpeg"])

        stored = [file for file in self.form.stored_files() if file.field_key == 'FOTOS0']

        assert [file.file_url for file in stored] == ["https://bucket/a.jpeg", "https://bucket/b.jpeg"]
        assert [file.file_index for file in stored] == [0, 1]

    def test_enumera_url_unica_como_string(self):
        self._with_file_field("https://bucket/unica.jpeg")

        stored = [file for file in self.form.stored_files() if file.field_key == 'FOTOS0']

        assert len(stored) == 1
        assert stored[0].file_index == 0

    def test_ignora_upload_que_ainda_nao_virou_url(self):
        # dict é o payload de upload recebido no submit, antes da presigned.
        self._with_file_field([{"filename": "a.jpg", "mimetype": "image/jpeg"}])

        assert [file for file in self.form.stored_files() if file.field_key == 'FOTOS0'] == []

    def test_registra_a_instancia_da_secao_duplicada(self):
        self._with_file_field(["https://bucket/a.jpeg"], section_id=3, section_instance=2)

        stored = [file for file in self.form.stored_files() if file.field_key == 'FOTOS0']

        assert stored[0].section_id == 3
        assert stored[0].section_instance == 2

    def test_inclui_a_imagem_da_justificativa(self):
        self._with_file_field(["https://bucket/a.jpeg"])

        urls = [file.file_url for file in self.form.stored_files() if file.field_key is None]

        # O mock traz a justificativa preenchida com image_url='image'.
        assert urls == ['image']
