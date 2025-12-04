import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_form.app.get_form_viewmodel import GetFormViewmodel
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetFormViewmodel:
    def test_get_form_viewmodel(self):
        repo = FormRepositoryMock()
        form = repo.forms[0]

        viewmodel = GetFormViewmodel(form).to_dict()

        assert viewmodel['id'] == form.id
        assert viewmodel['status'] == form.status.value
        assert viewmodel['sessions'][0]['section_id'] == form.sections[0].section_id
        assert viewmodel['justification']['options'][0]['option'] == form.justification.options[0].option
        assert viewmodel['priority'] == form.priority.value
        assert viewmodel['observation'] == form.observation
        assert viewmodel['created_by'] == form.created_by
        assert viewmodel['created_at'] == form.created_at
        assert viewmodel['in_progress_at'] == form.in_progress_at
        assert viewmodel['completed_at'] == form.completed_at
        assert viewmodel['cancelled_at'] == form.cancelled_at
