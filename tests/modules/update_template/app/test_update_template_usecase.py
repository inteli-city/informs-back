import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.append(os.getcwd())

from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestUpdateTemplateUsecase:
    def setup_method(self):
        self.repo = TemplateRepositoryMock()
        self.usecase = UpdateTemplateUsecase(self.repo)
        self.existing = self.repo.templates[0]

    def test_update_template_success_partial(self):
        updated = self.usecase(
            template_id=self.existing.id,
            requester_user_id="user-1",
            name="Updated Name",
            description="New desc",
        )

        assert updated.name == "Updated Name"
        assert updated.description == "New desc"
        assert updated.system == self.existing.system
        assert updated.sections == self.existing.sections
        assert isinstance(updated.updated_at, int)

    def test_update_template_with_sessions(self):
        new_section = Section(section_id=2, fields=[TextField(label="Other", required=True, key="other", order=1)])
        updated = self.usecase(
            template_id=self.existing.id,
            requester_user_id="user-1",
            sessions=[new_section],
            is_active=False,
        )
        assert updated.sections[0].section_id == 2
        assert updated.is_active is False

    def test_update_template_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                template_id="non-existent",
                requester_user_id="user-1",
                name="Any",
            )

    def test_update_template_invalid_sessions(self):
        with pytest.raises(EntityError):
            self.usecase(
                template_id=self.existing.id,
                requester_user_id="user-1",
                sessions=[],
            )
