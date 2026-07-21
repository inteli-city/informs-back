import os
import sys
import uuid

import pytest

sys.path.append(os.getcwd())

from src.modules.get_template.app.get_template_usecase import GetTemplateUsecase
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestGetTemplateUsecase:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = GetTemplateUsecase(self.repo)
        self.template = self.repo.templates[0]
        self.requester = UserGatewayDTO(user_id="user-123", name="User", email="user@test.com", systems=[self.template.system])

    def test_get_template_usecase_success(self):
        template = self.usecase(template_id=self.template.id, requester=self.requester)

        assert template.id == self.template.id
        assert template.name == self.template.name

    def test_get_template_usecase_not_found(self):
        template_id = str(uuid.uuid4())
        with pytest.raises(NoItemsFound):
            self.usecase(template_id=template_id, requester=self.requester)

    def test_get_template_usecase_forbidden(self):
        other_requester = UserGatewayDTO(user_id="user-123", name="User", email="user@test.com", systems=["ORION"])
        with pytest.raises(ForbiddenAction):
            self.usecase(template_id=self.template.id, requester=other_requester)

    def test_get_template_usecase_inactive(self):
        self.template.is_active = False
        with pytest.raises(NoItemsFound):
            self.usecase(template_id=self.template.id, requester=self.requester)
