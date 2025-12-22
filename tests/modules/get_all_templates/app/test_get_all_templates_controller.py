import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_all_templates.app.get_all_templates_controller import GetAllTemplatesController
from src.modules.get_all_templates.app.get_all_templates_usecase import GetAllTemplatesUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestGetAllTemplatesController:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = GetAllTemplatesUsecase(self.repo)
        self.controller = GetAllTemplatesController(self.usecase)

    def _make_requester(self):
        return {
            "sub": "user-123",
            "name": "User",
            "email": "user@test.com",
            "cognito:groups": "FORMULARIOS",
        }

    def test_get_all_templates_controller_success(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "page": 1,
            "limit": 20,
            "system": self.repo.templates[0].system,
            "isActive": True
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert len(response.body["templates"]) == 1
        assert response.body["templates"][0]["id"] == self.repo.templates[0].id

    def test_get_all_templates_controller_invalid_limit(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "page": 1,
            "limit": 10
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert "limit" in response.body

    def test_get_all_templates_controller_invalid_page(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "page": 0,
            "limit": 20
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: page"

    def test_get_all_templates_controller_invalid_is_active(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "page": 1,
            "limit": 20,
            "isActive": "maybe"
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: isActive"

    def test_get_all_templates_controller_invalid_system(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "page": 1,
            "limit": 20,
            "system": 123
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: system"

    def test_get_all_templates_controller_missing_requester(self):
        request = HttpRequest(body={"page": 1, "limit": 20})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"
