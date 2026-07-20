import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_form.app.get_form_controller import GetFormController
from src.modules.get_form.app.get_form_usecase import GetFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class TestGetFormController:
    def setup_method(self):
        self.repo = FormRepositoryMock()
        self.usecase = GetFormUsecase(self.repo)
        self.controller = GetFormController(self.usecase)
        self.form = self.repo.forms[0]

    def test_get_form_success(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.form.id
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert response.body["id"] == self.form.id

    def test_get_form_missing_requester(self):
        request = HttpRequest(body={"form_id": self.form.id})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'

    def test_get_form_missing_form_id(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            }
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'

    def test_get_form_wrong_type_form_id(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": 123
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Campo form_id deveria ser do tipo str, mas foi recebido um campo do tipo <class 'int'>"

    def test_get_form_forbidden(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": "another-user-id-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.form.id
        })

        response = self.controller(request)

        assert response.status_code == 403

    def test_get_form_forbidden_missing_formularios_group(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "SGC,INTELIFLEETS"
            },
            "form_id": self.form.id
        })

        response = self.controller(request)

        assert response.status_code == 403
        assert response.body == 'Ação não permitida: Usuário não esta apto para o sistema'

    def test_get_form_not_found(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": "non-existent-id-123456789012345678901234567890123456"
        })

        response = self.controller(request)

        assert response.status_code == 404

    def test_get_form_unexpected_error(self):
        class BoomUsecase:
            def __call__(self, requester_user_id: str, form_id: str):
                raise RuntimeError("boom")

        controller = GetFormController(BoomUsecase())
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.form.id
        })

        response = controller(request)

        assert response.status_code == 500
        assert response.body == "boom"
