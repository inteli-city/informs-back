import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.system_config_repository_mock import SystemConfigRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


def _make_base_body():
    return {
            "requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel@gmail.com",
                "cognito:groups": "FORMULARIOS,GAIA"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "latitude": 1.0,
            "longitude": 1.0,
            "priority": 3,
            "justifications": [
                {"option": "option", "required_image": True, "required_text": True}
            ],
            "sections": [
                {
                    "section_id": 1,
                    "fields": [
                        {
                            "field_type": "TEXT_FIELD",
                            "label": "placeholder",
                            "required": True,
                            "key": "key",
                            "order": 0,
                            "regex": "regex",
                            "max_length": 10
                        }
                    ]
                }
            ],
            "information_fields": [
                {"information_field_type": "TEXT_INFORMATION_FIELD", "value": "value"}
            ],
            "observation": "obs"
        }


class TestCreateFormController:
    def test_create_form_controller_success(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        request = HttpRequest(body=_make_base_body())
        response = controller(request)

        assert response.status_code == 201
        assert response.body["form_title"] == "FORM TITLE"
        assert response.body["user_id"] == "d61dbf66-a10f-11ed-a8fc-0242ac120001"
        assert len(response.body["sections"]) == 1
        assert response.body["files"] == []

    def test_create_form_controller_with_files(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["information_fields"] = [
            {
                "information_field_type": "FILE_INFORMATION_FIELD",
                "filename": "a.jpg",
                "mimetype": "image/jpeg"
            }
        ]
        request = HttpRequest(body=body)
        response = controller(request)

        assert response.status_code == 201
        assert len(response.body["files"]) == 1
        assert response.body["files"][0]["filename"] == "a.jpg"

    def test_create_form_controller_with_url_information_field(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["information_fields"] = [
            {
                "information_field_type": "URL_INFORMATION_FIELD",
                "url": "https://example.com/photo.jpg",
                "mimetype": "image/jpeg"
            }
        ]
        request = HttpRequest(body=body)
        response = controller(request)

        assert response.status_code == 201
        # URL não gera upload/presigned URL: aponta para um recurso já existente.
        assert response.body["files"] == []
        info = response.body["information_fields"][0]
        assert info["information_field_type"] == "URL_INFORMATION_FIELD"
        assert info["url"] == "https://example.com/photo.jpg"
        assert info["mimetype"] == "image/jpeg"

    def test_create_form_controller_without_information_fields(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("information_fields")
        request = HttpRequest(body=body)
        response = controller(request)

        assert response.status_code == 201
        assert response.body["information_fields"] is None
        assert response.body["files"] == []

    def test_create_form_controller_missing_requester(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("requester_user")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"

    def test_create_form_controller_missing_user_id(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("user_id")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: user_id"

    def test_create_form_controller_missing_system(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("system")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: system"

    def test_create_form_controller_missing_street(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("street")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: street"

    def test_create_form_controller_missing_city(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("city")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: city"

    def test_create_form_controller_missing_latitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("latitude")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: latitude"

    def test_create_form_controller_missing_longitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("longitude")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: longitude"

    def test_create_form_controller_missing_priority(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("priority")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: priority"

    def test_create_form_controller_missing_justifications(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("justifications")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: justifications"

    def test_create_form_controller_missing_sections(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.pop("sections")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: sections"

    def test_create_form_controller_missing_sections_with_uuid_template(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        template_repo = TemplateRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo, template_repo))

        body = _make_base_body()
        body["template"] = template_repo.templates[0].id
        body.pop("sections")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 201
        assert len(response.body["sections"]) == len(template_repo.templates[0].sections)

    def test_create_form_controller_template_not_found(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        template_repo = TemplateRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo, template_repo))

        body = _make_base_body()
        body["template"] = "d61dbf66-a10f-11ed-a8fc-0242ac1200ab"
        body.pop("sections")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 404
        assert response.body == "Template não encontrado"

    def test_create_form_controller_invalid_priority(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["priority"] = "INVALID"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "priority" in response.body

    def test_create_form_controller_invalid_expiration_date(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["expiration_date"] = "invalid"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "expiration_date" in response.body

    def test_create_form_controller_invalid_latitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["latitude"] = "invalid"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "latitude" in response.body

    def test_create_form_controller_duplicated_field_key(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["sections"] = [
            {
                "section_id": 1,
                "fields": [
                    {
                        "field_type": "TEXT_FIELD",
                        "label": "field 1",
                        "required": True,
                        "key": "duplicate_key",
                        "order": 0,
                    },
                    {
                        "key": "duplicate_key",
                        "order": 1,
                        "label": "field 2",
                        "required": True,
                        "field_type": "TEXT_FIELD",
                    }
                ],
            }
        ]
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "Chaves de campo duplicadas na seção" in response.body

    def test_create_form_controller_forbidden_system(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["requester_user"]["cognito:groups"] = "FORMULARIOS,ORION"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 403
        assert "permissão" in response.body


class TestCreateFormControllerUberlandiaPool:
    """Especificação Uberlândia §6/§9.1: `user_id` opcional (pool) + campos novos."""

    def test_missing_user_id_with_allow_unassigned_forms_creates_pool_form(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        system_config_repo = SystemConfigRepositoryMock()
        system_config_repo.put(SystemConfig(system="GAIA", created_at=1, updated_at=1, allow_unassigned_forms=True))
        controller = CreateFormController(CreateFormUsecase(repo, file_repo, system_config_repo=system_config_repo))

        body = _make_base_body()
        body.pop("user_id")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 201
        assert response.body["user_id"] is None

    def test_invalid_origin_returns_bad_request(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body["origin"] = "NOT_A_VALID_ORIGIN"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400

    def test_new_fields_are_returned_in_response(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = _make_base_body()
        body.update(
            external_id="OS-7514",
            origin="CITIZEN",
            service_type="tapa-buraco",
            occurred_at=1,
            scheduled_start_at=2,
            scheduled_end_at=3,
            attributes={"bairro": ["Santa Mônica"]},
        )
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 201
        assert response.body["external_id"] == "OS-7514"
        assert response.body["origin"] == "CITIZEN"
        assert response.body["service_type"] == "tapa-buraco"
        assert response.body["attributes"] == {"bairro": ["Santa Mônica"]}
