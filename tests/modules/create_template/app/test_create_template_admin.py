import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import ADMIN_ROLE_ID, SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock

PLATFORM_ADMIN = "d61dbf66-a10f-11ed-a8fc-0242ac120001"  # super admin no mock
INSPECTOR = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
REASONS = [JustificationOption(option="Local inacessível", required_image=True, required_text=False)]


def _sections():
    return [Section(section_id=1, fields=[TextField(label="Nome", required=True, key="nome", order=1)])]


class TestTemplateAdminRules:
    def setup_method(self):
        self.templates = TemplateRepositoryMock()
        self.profiles = ProfileRepositoryMock()
        self.roles = SystemRoleRepositoryMock()
        self.access_control = AccessControl(self.profiles, self.roles)
        self.create = CreateTemplateUsecase(self.templates, self.access_control)

    def _join(self, user_id, system, role_id):
        self.profiles.put_membership(SystemMembership(
            user_id=user_id, system=system, role_id=role_id, created_at=1, updated_at=1,
        ))

    def _create(self, user_id, system="GAIA", **extra):
        return self.create(created_by=user_id, name="Vistoria", system=system, description=None,
                           is_active=True, sections=_sections(), **extra)

    def test_inspector_without_templates_manage_cannot_create(self):
        with pytest.raises(ForbiddenAction):
            self._create(INSPECTOR)

    def test_system_admin_creates_template_of_own_system(self):
        self._join(INSPECTOR, "GAIA", ADMIN_ROLE_ID)
        assert self._create(INSPECTOR).system == "GAIA"

    def test_role_with_templates_manage_creates_template(self):
        self.roles.put_role(SystemRole(
            system="GAIA", role_id="r-templates", name="Templates", actions=[Action.TEMPLATES_MANAGE],
            created_at=1, updated_at=1,
        ))
        self._join(INSPECTOR, "GAIA", "r-templates")
        assert self._create(INSPECTOR).system == "GAIA"

    def test_system_admin_cannot_move_template_to_another_system(self):
        self._join(INSPECTOR, "GAIA", ADMIN_ROLE_ID)
        template = self._create(INSPECTOR)
        with pytest.raises(ForbiddenAction):
            UpdateTemplateUsecase(self.templates, self.access_control)(
                template_id=template.id, requester_user_id=INSPECTOR, system="UBERLANDIA"
            )

    def test_template_keeps_cancellation_reasons(self):
        template = self._create(PLATFORM_ADMIN, justification_options=REASONS)
        stored = TemplateDynamoDTO.from_dynamo({"PK": f"template#{template.id}", **TemplateDynamoDTO.from_entity(template).to_dynamo()}).to_entity()
        assert [option.option for option in stored.justification_options] == ["Local inacessível"]

    def test_update_replaces_cancellation_reasons(self):
        template = self._create(PLATFORM_ADMIN, justification_options=REASONS)
        updated = UpdateTemplateUsecase(self.templates, self.access_control)(
            template_id=template.id, requester_user_id=PLATFORM_ADMIN, justification_options=[]
        )
        assert updated.justification_options == []

    def test_repeated_reasons_are_rejected(self):
        with pytest.raises(EntityError):
            self._create(PLATFORM_ADMIN, justification_options=REASONS + REASONS)
