import os
import sys
import uuid

import pytest

sys.path.append(os.getcwd())

from src.modules.get_template.app.get_template_usecase import GetTemplateUsecase
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestGetTemplateUsecase:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = GetTemplateUsecase(self.repo)
        self.template = self.repo.templates[0]

    def test_get_template_usecase_success(self):
        template = self.usecase(template_id=self.template.id)

        assert template.id == self.template.id
        assert template.name == self.template.name

    def test_get_template_usecase_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(template_id=str(uuid.uuid4()))
