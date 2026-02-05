import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_controller import CreateTemplateController
from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestCreateTemplateController:
    def _make_base_body(self):
        return {
            "requester_user": {
                "sub": "user-123",
                "name": "User",
                "email": "user@test.com",
                "cognito:groups": "FORMULARIOS",
            },
            "name": "Template X",
            "system": "GAIA",
            "description": "Description",
            "is_active": True,
            "sections": [
                {
                    "section_id": 1,
                    "fields": [
                        {
                            "field_type": "TEXT_FIELD",
                            "label": "Name",
                            "required": True,
                            "key": "name",
                            "order": 0,
                        }
                    ],
                }
            ],
        }

    def test_create_template_controller_success(self):
        repo = TemplateRepositoryMock()
        controller = CreateTemplateController(CreateTemplateUsecase(repo))

        request = HttpRequest(body=self._make_base_body())
        response = controller(request)

        assert response.status_code == 201
        assert response.body["name"] == "Template X"
        assert response.body["system"] == "GAIA"
        assert len(response.body["sections"]) == 1

    def test_create_template_controller_missing_name(self):
        repo = TemplateRepositoryMock()
        controller = CreateTemplateController(CreateTemplateUsecase(repo))

        body = self._make_base_body()
        body.pop("name")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: name"

    def test_create_template_controller_wrong_type_is_active(self):
        repo = TemplateRepositoryMock()
        controller = CreateTemplateController(CreateTemplateUsecase(repo))

        body = self._make_base_body()
        body["is_active"] = "true"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Campo is_active deveria ser do tipo bool, mas foi recebido um campo do tipo <class 'str'>"

    def test_create_template_controller_invalid_sections(self):
        repo = TemplateRepositoryMock()
        controller = CreateTemplateController(CreateTemplateUsecase(repo))

        body = self._make_base_body()
        body["sections"] = []
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: sections"
