import os
import sys

sys.path.append(os.getcwd())

from src.modules.start_form.app.start_form_viewmodel import StartFormViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_StartFormViewmodel:
    def test_start_form_viewmodel(self):
        repo = FormRepositoryMock()
        form = repo.forms[2]
        form.status = FORM_STATUS.IN_PROGRESS
        form.in_progress_at = 111
        form.updated_at = 222

        viewmodel = StartFormViewmodel(form)
        result = viewmodel.to_dict()

        assert result["id"] == form.id
        assert result["status"] == FORM_STATUS.IN_PROGRESS.value
        assert result["in_progress_at"] == 111
        assert result["updated_at"] == 222
