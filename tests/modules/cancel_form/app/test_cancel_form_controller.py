from src.modules.cancel_form.app.cancel_form_controller import CancelFormController
from src.modules.cancel_form.app.cancel_form_usecase import CancelFormUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock


class Test_CancelFormController:

    def test_cancel_form_controller(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        form_repo.forms[0].status = FORM_STATUS.IN_PROGRESS

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": form_repo.forms[0].id,
            "option": "option",
            "text": "justification_test",
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })

        response = controller(data)

        assert response.status_code == 200
        assert response.body["files"][0]["filename"] == "a.jpg"
    
    def test_cancel_form_controller_missing_request_user(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"form_id": form_repo.forms[0].id,
            "option": "option",
            "text": "justification_test",
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'
    
    def test_cancel_form_controller_missing_form_id(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "option": "option",
            "text": "justification_test",
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'
    
    def test_cancel_form_controller_missing_selected_option(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": form_repo.forms[0].id,
            "text": "justification_test",
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })
    
        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: option'
    
    def test_cancel_form_controller_wrong_type_selected_option(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": form_repo.forms[0].id,
            "option": 123,
            "text": "justification_test",
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo option deveria ser do tipo str, mas foi recebido um campo do tipo <class \'int\'>'
    
    def test_cancel_form_controller_wrong_type_justification_text(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": form_repo.forms[0].id,
            "option": "selected",
            "text": 123,
            "file": {"filename": "a.jpg", "mimetype": "image/png"}
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo text deveria ser do tipo str, mas foi recebido um campo do tipo <class \'int\'>'
    
    def test_cancel_form_controller_wrong_type_justification_image(self):
        form_repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = CancelFormUsecase(form_repo, file_repo)

        controller = CancelFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                "name": 'Gabriel Godoy',
                "email": 'gabriel@gmail.com',
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_id": form_repo.forms[0].id,
            "option": "selected",
            "text": "justification_test",
            "file": 123
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == 'Campo file deveria ser do tipo dict, mas foi recebido um campo do tipo <class \'int\'>'
