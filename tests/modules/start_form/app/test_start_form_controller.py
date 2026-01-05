import os
import sys

sys.path.append(os.getcwd())

from src.modules.start_form.app.start_form_controller import StartFormController
from src.modules.start_form.app.start_form_usecase import StartFormUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.queue_repository_mock import QueueRepositoryMock


class Test_StartFormController:
    def setup_method(self):
        self.repo = FormRepositoryMock()
        self.queue_repo = QueueRepositoryMock()
        self.usecase = StartFormUsecase(self.repo, self.queue_repo)
        self.controller = StartFormController(self.usecase)
        # Use the pending form fixture to keep tests isolated
        self.pending_form = self.repo.forms[2]
        self.pending_form.status = FORM_STATUS.PENDING

    def test_start_form_controller_success(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.pending_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.pending_form.id,
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 204
        assert response.body == {}
        assert self.pending_form.status == FORM_STATUS.IN_PROGRESS
        assert self.pending_form.in_progress_at == 123456789

    def test_start_form_controller_missing_requester_user(self):
        request = HttpRequest(body={
            "form_id": self.pending_form.id,
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: requester_user'

    def test_start_form_controller_missing_form_id(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.pending_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: form_id'

    def test_start_form_controller_missing_in_progress_at(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.pending_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.pending_form.id,
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == 'Parâmetro ausente: in_progress_at'

    def test_start_form_controller_wrong_type_in_progress_at(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.pending_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.pending_form.id,
            "in_progress_at": "invalid",
        })

        response = self.controller(request)

        assert response.status_code == 400
        assert response.body == "Campo in_progress_at deveria ser do tipo int, mas foi recebido um campo do tipo <class 'str'>"

    def test_start_form_controller_wrong_user(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": "another-user",
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": self.pending_form.id,
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 403
        assert response.body == 'Ação não permitida: Usuário não é o preenchedor deste formulário'

    def test_start_form_controller_status_not_pending(self):
        in_progress_form = self.repo.forms[0]
        request = HttpRequest(body={
            "requester_user": {
                "sub": in_progress_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": in_progress_form.id,
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 403
        assert response.body == 'Ação não permitida: Formulário não está aberto para início'

    def test_start_form_controller_not_found(self):
        request = HttpRequest(body={
            "requester_user": {
                "sub": self.pending_form.user_id,
                "name": "Tester",
                "email": "tester@example.com",
                "cognito:groups": "FORMULARIOS"
            },
            "form_id": "non-existent",
            "in_progress_at": 123456789,
        })

        response = self.controller(request)

        assert response.status_code == 404
        assert response.body == 'Formulário não encontrado'
