import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock


class Test_CreateFormController:
    def _make_base_body(self):
        return {
            "requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel@gmail.com",
                "cognito:groups": "FORMULARIOS"
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

    def test_create_form_controller_success(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        request = HttpRequest(body=self._make_base_body())
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

        body = self._make_base_body()
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

    def test_create_form_controller_missing_requester(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("requester_user")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"

    def test_create_form_controller_missing_user_id(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("user_id")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: user_id"

    def test_create_form_controller_missing_system(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("system")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: system"

    def test_create_form_controller_missing_street(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("street")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: street"

    def test_create_form_controller_missing_city(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("city")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: city"

    def test_create_form_controller_missing_latitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("latitude")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: latitude"

    def test_create_form_controller_missing_longitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("longitude")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: longitude"

    def test_create_form_controller_missing_priority(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("priority")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: priority"

    def test_create_form_controller_missing_justifications(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("justifications")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: justifications"

    def test_create_form_controller_missing_sections(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body.pop("sections")
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: sections"

    def test_create_form_controller_invalid_priority(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body["priority"] = "INVALID"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "priority" in response.body

    def test_create_form_controller_invalid_expiration_date(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body["expiration_date"] = "invalid"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "expiration_date" in response.body

    def test_create_form_controller_invalid_latitude(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
        body["latitude"] = "invalid"
        request = HttpRequest(body=body)

        response = controller(request)
        assert response.status_code == 400
        assert "latitude" in response.body

    def test_create_form_controller_duplicated_field_key(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        controller = CreateFormController(CreateFormUsecase(repo, file_repo))

        body = self._make_base_body()
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
        assert "duplicated field key(s)" in response.body
