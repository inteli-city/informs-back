import os
import sys
from datetime import datetime

import pytest

sys.path.append(os.getcwd())

from src.modules.start_form.app.start_form_usecase import StartFormUsecase
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class TestStartFormUsecase:
    def test_start_form_success(self):
        repo = FormRepositoryMock()
        usecase = StartFormUsecase(repo)

        form = repo.forms[0]
        form.status = FormStatus.PENDING

        usecase(
            requester_user_id=form.user_id,
            form_id=form.id,
            in_progress_at=int(datetime.now().timestamp() * 1000)
        )

        assert form.status == FormStatus.IN_PROGRESS
        assert form.in_progress_at is not None

    def test_start_form_wrong_user(self):
        repo = FormRepositoryMock()
        usecase = StartFormUsecase(repo)

        form = repo.forms[0]
        form.status = FormStatus.PENDING

        with pytest.raises(ForbiddenAction):
            usecase(
                requester_user_id="another-user",
                form_id=form.id,
                in_progress_at=int(datetime.now().timestamp() * 1000)
            )

    def test_start_form_not_found(self):
        repo = FormRepositoryMock()
        usecase = StartFormUsecase(repo)

        with pytest.raises(NoItemsFound):
            usecase(
                requester_user_id="d61dbf66-a10f-11ed-a8fc-0242ac120099",
                form_id="not-found",
                in_progress_at=int(datetime.now().timestamp() * 1000)
            )
