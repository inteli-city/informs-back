from src.modules.submit_form.app.submit_form_controller import SubmitFormController
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock


class Test_SubmitFormController:

    def _build_fields(self):
        return [
            {
                "section_id": 1,
                "field_key": "key",
                "value": "poggers"
            }
        ]

    def test_submit_form_controller(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "completed_at": 123,
            "fields": self._build_fields(),
        })

        response = controller(data)

        assert response.status_code == 200
        assert response.body["files"] == []
    
    def test_submit_form_controller_missing_requester_user(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={
            "form_id": repo.forms[0].id,
            "fields": self._build_fields(),
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'
        assert response.body == 'Parâmetro ausente: requester_user'
    
    def test_submit_form_controller_missing_form_id(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "fields": self._build_fields(),
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'

    def test_submit_form_controller_missing_fields(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: fields'
    
    def test_submit_form_controller_wrong_type_fields(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "fields": 'fields',
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo fields deveria ser do tipo list, mas foi recebido um campo do tipo <class \'str\'>'
    
    def test_submit_form_controller_fields_empty(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "fields": [],
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: fields'

    def test_submit_form_controller_missing_completed_at(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "fields": self._build_fields(),
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: completed_at'

    def test_submit_form_controller_wrong_type_completed_at(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "fields": self._build_fields(),
            "completed_at": "invalid",
        })

        response = controller(data)

        assert response.status_code == 400
