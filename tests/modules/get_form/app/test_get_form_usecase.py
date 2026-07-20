import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.get_form.app.get_form_usecase import GetFormUsecase
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class TestGetFormUsecase:
    def test_get_form_success(self):
        repo = FormRepositoryMock()
        usecase = GetFormUsecase(repo)

        form = repo.forms[0]

        result = usecase(requester_user_id=form.user_id, form_id=form.id)

        assert result.id == form.id
        assert result.status == form.status

    def test_get_form_not_found(self):
        repo = FormRepositoryMock()
        usecase = GetFormUsecase(repo)

        with pytest.raises(NoItemsFound):
            usecase(requester_user_id=repo.forms[0].user_id, form_id="non-existent-id-123456789012345678901234567890123456")

    def test_get_form_forbidden(self):
        repo = FormRepositoryMock()
        usecase = GetFormUsecase(repo)

        form = repo.forms[0]

        with pytest.raises(ForbiddenAction):
            usecase(requester_user_id="another-user-id-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", form_id=form.id)
