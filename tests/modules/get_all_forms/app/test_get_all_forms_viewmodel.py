import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_all_forms.app.get_all_forms_viewmodel import GetAllFormsViewmodel, FormItemViewmodel
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetAllFormsViewmodel:
    def test_get_all_forms_viewmodel(self):
        repo = FormRepositoryMock()
        form = repo.forms[0]

        viewmodel = GetAllFormsViewmodel(forms=[form], limit=20, last_evaluated_key=None)
        result = viewmodel.to_dict()

        assert result["limit"] == 20
        assert result["last_evaluated_key"] is None
        assert len(result["forms"]) == 1
        assert result["forms"][0]["id"] == form.id
        assert result["forms"][0]["status"] == form.status.value
