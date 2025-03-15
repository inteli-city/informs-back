from src.modules.update_form_status.app.update_form_status_controller import UpdateFormStatusController
from src.modules.update_form_status.app.update_form_status_usecase import UpdateFormStatusUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_UpdateFormStatusController:

    def test_update_form_status_controller(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[2].form_id,
            "status": "IN_PROGRESS",
        })

        response = controller(data)

        assert response.status_code == 200
        assert response.body['message'] == 'Status do formulário atualizado com sucesso!'
    
    def test_update_form_status_controller_missing_request_user(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"form_id": repo.forms[0].form_id,
            "status": "IN_PROGRESS",
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'


    def test_update_form_status_controller_missing_form_id(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "status": "IN_PROGRESS",
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'
    
    def test_update_form_status_controller_missing_status(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: status'
    
    def test_update_form_status_controller_invalid_status(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": repo.forms[0].form_id,
            "status": "123",
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro inválido: status'
    

    def test_update_form_status_controller_no_items_found(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)
        controller = UpdateFormStatusController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": 'd61dbf66-a10f-11ed-a8fc-0242ac120099',
            "status": "IN_PROGRESS",
        })

        response = controller(data)

        assert response.status_code == 404
        assert response.body == 'Formulário não encontrado'