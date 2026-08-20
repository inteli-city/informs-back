import os

from src.modules.refresh_presign.app.refresh_presign_controller import RefreshPresignController
from src.modules.refresh_presign.app.refresh_presign_usecase import RefreshPresignUsecase
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.helpers.functions.s3_url import build_s3_url
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

os.environ["STAGE"] = "TEST"


class TestRefreshPresignController:

    def setup_method(self):
        self.repo = FormRepositoryMock()
        self.controller = RefreshPresignController(
            RefreshPresignUsecase(self.repo, FileRepositoryMock())
        )
        self.form = self.repo.forms[0]
        self.file_url = build_s3_url(f"2026/system/{self.form.id}/sections/1/0/aaa.jpeg")
        self.form.sections = [
            Section(section_id=1, fields=[FileField(
                label='fotos', required=False, key='FOTOS0', order=1,
                file_type=FileType.IMAGE, value=[self.file_url],
            )])
        ]

    def _request(self, **overrides):
        body = {
            "requester_user": {
                "sub": self.form.user_id,
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "FORMULARIOS",
            },
            "form_id": self.form.id,
            "files": [{"file_url": self.file_url, "mimetype": "image/jpeg"}],
        }
        body.update(overrides)
        return HttpRequest(body=body)

    def test_renova_presigned_com_sucesso(self):
        response = self.controller(self._request())

        assert response.status_code == 200
        assert len(response.body["files"]) == 1
        assert response.body["files"][0]["file_url"] == self.file_url
        assert response.body["files"][0]["pre_signed_url"] != self.file_url

    def test_lista_vazia_e_rejeitada_no_contrato(self):
        response = self.controller(self._request(files=[]))

        assert response.status_code == 400

    def test_arquivo_sem_mimetype_e_rejeitado(self):
        response = self.controller(self._request(files=[{"file_url": self.file_url}]))

        assert response.status_code == 400

    def test_formulario_inexistente(self):
        response = self.controller(self._request(form_id="nao-existe"))

        assert response.status_code == 404

    def test_arquivo_de_outro_formulario(self):
        response = self.controller(self._request(
            files=[{"file_url": build_s3_url("2026/system/outro/sections/1/0/zzz.jpeg"), "mimetype": "image/jpeg"}]
        ))

        assert response.status_code == 404
