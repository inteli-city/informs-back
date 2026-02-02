import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetAllFormsUsecase:
    def test_get_all_forms_usecase_filter_by_user(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(
            user_id=repo.forms[0].user_id,
            name="User",
            email="user@test.com",
            systems=[repo.forms[0].system],
        )

        forms, next_key = usecase(
            requester=requester,
            limit=20
        )

        assert len(forms) == 2
        assert all(form.user_id == repo.forms[0].user_id for form in forms)
        assert next_key is None

    def test_get_all_forms_usecase_filter_by_status(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(
            user_id=repo.forms[0].user_id,
            name="User",
            email="user@test.com",
            systems=[repo.forms[0].system],
        )

        forms, next_key = usecase(
            requester=requester,
            limit=20,
            status=FORM_STATUS.PENDING
        )

        assert len(forms) == 1
        assert forms[0].status == FORM_STATUS.PENDING
        assert next_key is None
