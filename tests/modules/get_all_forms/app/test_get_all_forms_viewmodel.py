import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_all_forms.app.get_all_forms_viewmodel import GetAllFormsViewmodel, FormItemViewmodel
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetAllFormsViewmodel:
    def test_get_all_forms_viewmodel(self):
        repo = FormRepositoryMock()
        form = repo.forms[0]

        viewmodel = GetAllFormsViewmodel(forms=[form], page=1, limit=20)
        result = viewmodel.to_dict()

        assert result["page"] == 1
        assert result["limit"] == 20
        assert len(result["forms"]) == 1
        assert result["forms"][0]["id"] == form.id
        assert result["forms"][0]["status"] == form.status.value
