import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock

PLATFORM_ADMIN = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
REASONS = [JustificationOption(option="Local inacessível", required_image=True, required_text=False)]


def _sections():
    return [Section(section_id=1, fields=[TextField(label="Nome", required=True, key="nome", order=1)])]


class TestTemplateAdminRules:
    def setup_method(self):
        self.templates = TemplateRepositoryMock()
        self.profiles = ProfileRepositoryMock()
        self.create = CreateTemplateUsecase(self.templates, self.profiles)

    def _create(self, user_id, system="GAIA", **extra):
        return self.create(created_by=user_id, name="Vistoria", system=system, description=None,
                           is_active=True, sections=_sections(), **extra)

    def test_inspector_without_admin_systems_cannot_create(self):
        with pytest.raises(ForbiddenAction):
            self._create(INSPECTOR)

    def test_system_admin_creates_template_of_own_system(self):
        self.profiles.update_profile(user_id=INSPECTOR, admin_systems=["GAIA"])
        assert self._create(INSPECTOR).system == "GAIA"

    def test_system_admin_cannot_move_template_to_another_system(self):
        self.profiles.update_profile(user_id=INSPECTOR, admin_systems=["GAIA"])
        template = self._create(INSPECTOR)
        with pytest.raises(ForbiddenAction):
            UpdateTemplateUsecase(self.templates, self.profiles)(
                template_id=template.id, requester_user_id=INSPECTOR, system="UBERLANDIA"
            )

    def test_template_keeps_cancellation_reasons(self):
        template = self._create(PLATFORM_ADMIN, justification_options=REASONS)
        stored = TemplateDynamoDTO.from_dynamo({"PK": f"template#{template.id}", **TemplateDynamoDTO.from_entity(template).to_dynamo()}).to_entity()
        assert [option.option for option in stored.justification_options] == ["Local inacessível"]

    def test_update_replaces_cancellation_reasons(self):
        template = self._create(PLATFORM_ADMIN, justification_options=REASONS)
        updated = UpdateTemplateUsecase(self.templates, self.profiles)(
            template_id=template.id, requester_user_id=PLATFORM_ADMIN, justification_options=[]
        )
        assert updated.justification_options == []

    def test_repeated_reasons_are_rejected(self):
        with pytest.raises(EntityError):
            self._create(PLATFORM_ADMIN, justification_options=REASONS + REASONS)
