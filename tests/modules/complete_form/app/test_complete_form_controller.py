from src.modules.complete_form.app.complete_form_controller import CompleteFormController
from src.modules.complete_form.app.complete_form_usecase import CompleteFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock


class Test_CompleteFormController:

    def test_complete_form_controller(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "sections": [
                {
                    "section_id": "1",
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
            ],
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 200
        assert response.body['message'] == 'Formulário finalizado com sucesso!'
    
    def test_complete_form_controller_missing_requester_user(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={
            "form_id": repo.forms[0].form_id,
            "sections": [
                {
                    "section_id": "1",
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
            ],
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'
    
    def test_complete_form_controller_missing_form_id(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "sections": [
                {
                    "section_id": "1",
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
            ],
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'

    def test_complete_form_controller_missing_sections(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: sections'
    
    def test_complete_form_controller_wrong_type_sections(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "sections": 'sections',
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo sections deveria ser do tipo list, mas foi recebido um campo do tipo <class \'str\'>'
    
    def test_complete_form_controller_sections_empty(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "sections": [],
            "vinculation_form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120011"
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: sections'

    def test_complete_form_controller_wrong_type_vinculation_form_id(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        controller = CompleteFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "sections": [
                {
                    "section_id": "1",
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
            ],
            "vinculation_form_id": 123,
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo vinculation_form_id deveria ser do tipo str, mas foi recebido um campo do tipo <class \'int\'>'