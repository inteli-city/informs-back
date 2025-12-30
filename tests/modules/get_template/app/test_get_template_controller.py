import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.modules.get_template.app.get_template_controller import GetTemplateController
from src.modules.get_template.app.get_template_usecase import GetTemplateUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestGetTemplateController:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = GetTemplateUsecase(self.repo)
        self.controller = GetTemplateController(self.usecase)
        self.template = self.repo.templates[0]

    def _make_requester(self):
        return {
            "sub": "user-123",
            "name": "User",
            "email": "user@test.com",
            "cognito:groups": f"FORMULARIOS,{self.template.system}",
        }

    def test_get_template_controller_success(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "template_id": self.template.id
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert response.body["id"] == self.template.id

    def test_get_template_controller_missing_requester(self):
        request = HttpRequest(body={"template_id": self.template.id})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"

    def test_get_template_controller_missing_template_id(self):
        request = HttpRequest(body={"requester_user": self._make_requester()})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: template_id"

    def test_get_template_controller_wrong_type_template_id(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "template_id": 123
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Campo template_id deveria ser do tipo str, mas foi recebido um campo do tipo <class 'int'>"

    def test_get_template_controller_not_found(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "template_id": str(uuid.uuid4())
        })

        response = self.controller(request)

        assert response.status_code == 404
        assert response.body == "Template não encontrado"

    def test_get_template_controller_forbidden(self):
        requester = {
            "sub": "user-123",
            "name": "User",
            "email": "user@test.com",
            "cognito:groups": "FORMULARIOS,ORION",
        }
        request = HttpRequest(body={
            "requester_user": requester,
            "template_id": self.template.id
        })

        response = self.controller(request)

        assert response.status_code == 403

    def test_get_template_controller_inactive(self):
        self.template.is_active = False
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "template_id": self.template.id
        })

        response = self.controller(request)

        assert response.status_code == 404
