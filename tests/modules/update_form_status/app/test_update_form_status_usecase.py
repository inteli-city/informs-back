import pytest
from src.modules.update_form_status.app.update_form_status_usecase import UpdateFormStatusUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock

class Test_UpdateFormStatusUseCase:

    def test_update_form_status_usecase(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        form = repo.forms[2]
        user = UserGatewayDTO(
            email="gabriel@gmail.com", name="Gabriel Godoy", user_id="d61dbf66-a10f-11ed-a8fc-0242ac120001", systems=["GAIA","JUNDIAI"]
        )

        result = usecase(user, form.form_id, FORM_STATUS.IN_PROGRESS)

        assert result.status == FORM_STATUS.IN_PROGRESS
        assert result.start_date is not None
    
    def test_update_form_status_usecase_go_back(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        form = repo.forms[0]
        user = UserGatewayDTO(
            email="gabriel@gmail.com", name="Gabriel Godoy", user_id="d61dbf66-a10f-11ed-a8fc-0242ac120001", systems=["GAIA","JUNDIAI"]
        )

        result = usecase(user, form.form_id, FORM_STATUS.PENDING)

        assert result.status == FORM_STATUS.PENDING
        assert result.start_date is None
    
    def test_update_form_status_usecase_same_status(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        form = repo.forms[0]
        user = UserGatewayDTO(
            email="gabriel@gmail.com", name="Gabriel Godoy", user_id="d61dbf66-a10f-11ed-a8fc-0242ac120001", systems=["GAIA","JUNDIAI"]
        )

        with pytest.raises(DuplicatedItem):
            usecase(user, form.form_id, FORM_STATUS.IN_PROGRESS)
    
    def test_update_form_status_usecase_form_not_found(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)
        user = UserGatewayDTO(
            email="gabriel@gmail.com", name="Gabriel Godoy", user_id="d61dbf66-a10f-11ed-a8fc-0242ac120001", systems=["GAIA","JUNDIAI"]
        )


        with pytest.raises(NoItemsFound):
            usecase(user, '123', FORM_STATUS.IN_PROGRESS)
    
    def test_update_form_status_usecase_user_not_owner(self):
        repo = FormRepositoryMock()
        usecase = UpdateFormStatusUsecase(repo)

        form = repo.forms[0]
        user = UserGatewayDTO(
            email="gabriel@gmail.com", name="Gabriel Godoy", user_id="d61dbf66-a10f-11ed-a8fc-0242ac120002", systems=["GAIA","JUNDIAI"]
        )

        with pytest.raises(ForbiddenAction):
            usecase(user, form.form_id, FORM_STATUS.IN_PROGRESS)
    


        
