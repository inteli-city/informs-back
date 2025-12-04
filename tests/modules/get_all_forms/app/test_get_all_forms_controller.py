import os
import sys

sys.path.append(os.getcwd())
from src.modules.get_all_forms.app.get_all_forms_controller import GetAllFormsController
from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetAllFormsController:
    def test_get_all_forms_controller_success(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id,
                "name": "User",
                "email": "user@test.com",
                "cognito:groups": "FORMULARIOS"
            },
            "page": 1,
            "limit": 20,
            "status": "PENDING",
            "system": repo.forms[0].system
        })

        response = controller(request)

        assert response.status_code == 200
        assert len(response.body["forms"]) == 1
        assert response.body["forms"][0]["status"] == "PENDING"

    def test_get_all_forms_controller_invalid_limit(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        controller = GetAllFormsController(usecase)

        request = HttpRequest(body={
            "requester_user": {
                "sub": repo.forms[0].user_id,
                "name": "User",
                "email": "user@test.com",
                "cognito:groups": "FORMULARIOS"
            },
            "page": 1,
            "limit": 10
        })

        response = controller(request)

        assert response.status_code == 400
        assert "limit" in response.body
