from src.modules.submit_form.app.submit_form_controller import SubmitFormController
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock
from src.shared.infra.repositories.queue_repository_mock import QueueRepositoryMock


class Test_SubmitFormController:

    def _build_sections(self):
        return [
            {
                "section_id": 1,
                "fields": [
                    {
                        "field_type": "TEXT_FIELD",
                        "placeholder": "placeholder",
                        "required": True,
                        "key": "key",
                        "regex": "regex",
                        "formatting": "formatting",
                        "max_length": 10,
                        "value": "poggers"
                    }
                ]
            }
        ]

    def test_submit_form_controller(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "completed_at": 123,
            "sections": self._build_sections(),
        })

        response = controller(data)

        assert response.status_code == 200
        assert response.body["images"] == []
    
    def test_submit_form_controller_missing_requester_user(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={
            "form_id": repo.forms[0].id,
            "sections": self._build_sections(),
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'
        assert response.body == 'Parâmetro ausente: requester_user'
    
    def test_submit_form_controller_missing_form_id(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "sections": self._build_sections(),
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'

    def test_submit_form_controller_missing_sections(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

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
        assert response.body == 'Parâmetro ausente: sections'
    
    def test_submit_form_controller_wrong_type_sections(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "sections": 'sections',
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo sections deveria ser do tipo list, mas foi recebido um campo do tipo <class \'str\'>'
    
    def test_submit_form_controller_sections_empty(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "sections": [],
            "completed_at": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: sections'

    def test_submit_form_controller_missing_completed_at(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "sections": self._build_sections(),
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: completed_at'

    def test_submit_form_controller_wrong_type_completed_at(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        controller = SubmitFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].id,
            "sections": self._build_sections(),
            "completed_at": "invalid",
        })

        response = controller(data)

        assert response.status_code == 400
