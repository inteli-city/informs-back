import os
import sys
import uuid

sys.path.append(os.getcwd())

from src.modules.get_all_templates.app.get_all_templates_controller import GetAllTemplatesController
from src.modules.get_all_templates.app.get_all_templates_usecase import GetAllTemplatesUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.domain.entities.template import Template
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock
from src.shared.helpers.functions.pagination_token import decode_pagination_token


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
            "cognito:groups": "FORMULARIOS,GAIA",
        }

    def test_get_all_templates_controller_success(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "limit": 20,
            "system": self.repo.templates[0].system,
            "isActive": True
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert len(response.body["templates"]) == 1
        assert response.body["templates"][0]["id"] == self.repo.templates[0].id
        assert response.body["system"] == self.repo.templates[0].system

    def test_get_all_templates_controller_invalid_limit(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "limit": 0,
            "system": self.repo.templates[0].system
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert "limit" in response.body

    def test_get_all_templates_controller_invalid_is_active(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "limit": 20,
            "isActive": "maybe",
            "system": self.repo.templates[0].system
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: isActive"

    def test_get_all_templates_controller_invalid_system(self):
        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "limit": 20,
            "system": 123
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: system"

    def test_get_all_templates_controller_missing_requester(self):
        request = HttpRequest(body={"limit": 20, "system": "GAIA"})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"

    def test_get_all_templates_controller_missing_system(self):
        request = HttpRequest(body={"limit": 20, "requester_user": self._make_requester()})

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: system"

    def test_get_all_templates_controller_forbidden_system(self):
        requester = {
            "sub": "user-123",
            "name": "User",
            "email": "user@test.com",
            "cognito:groups": "FORMULARIOS,ORION",
        }
        request = HttpRequest(body={
            "requester_user": requester,
            "limit": 20,
            "system": "GAIA"
        })

        response = self.controller(request)

        assert response.status_code == 403

    def test_get_all_templates_controller_pagination_key(self):
        # add extra template to exceed limit
        base = self.repo.templates[0]
        duplicated = Template(
            id=str(uuid.uuid4()),
            name=f"{base.name} 2",
            system=base.system,
            description=base.description,
            is_active=base.is_active,
            created_by=base.created_by,
            created_at=base.created_at,
            updated_at=base.updated_at,
            sections=base.sections,
        )
        self.repo.templates.append(duplicated)

        request = HttpRequest(body={
            "requester_user": self._make_requester(),
            "limit": 1,
            "system": self.repo.templates[0].system
        })

        response = self.controller(request)

        assert response.status_code == 200
        assert "last_evaluated_key" in response.body
        assert isinstance(response.body["last_evaluated_key"], str)
        decoded = decode_pagination_token(response.body["last_evaluated_key"])
        assert isinstance(decoded, dict)
