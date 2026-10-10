import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.get_all_forms.app.get_all_forms_usecase import GetAllFormsUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.dtos.user_gateway import UserGatewayDTO
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock

ADMIN_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'  # seed do ProfileRepositoryMock (ADMIN)
INSPECTOR_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120002'  # seed do ProfileRepositoryMock (INSPECTOR)

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _pool_form(**overrides) -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    section = Section(section_id=1, fields=[text_field])
    base = dict(
        id='d61dbf66-a10f-11ed-a8fc-0242ac120040', form_title='FORM TITLE', created_by=ADMIN_ID, user_id=None,
        system='UBERLANDIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )
    base.update(overrides)
    return Form(**base)


class TestGetAllFormsUsecase:
    def test_get_all_forms_usecase_filter_by_user(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(
            user_id=repo.forms[0].user_id,
            name="User",
            email="user@test.com",
            systems=[repo.forms[0].system],
        )

        forms, next_key = usecase(
            requester=requester,
            limit=20
        )

        assert len(forms) == 2
        assert all(form.user_id == repo.forms[0].user_id for form in forms)
        assert next_key is None

    def test_get_all_forms_usecase_filter_by_status(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(
            user_id=repo.forms[0].user_id,
            name="User",
            email="user@test.com",
            systems=[repo.forms[0].system],
        )

        forms, next_key = usecase(
            requester=requester,
            limit=20,
            status=FormStatus.PENDING
        )

        assert len(forms) == 1
        assert forms[0].status == FormStatus.PENDING
        assert next_key is None


class TestGetAllFormsUsecaseScope:
    """Especificação Uberlândia §6.3: scope=pool|mine|all."""

    def test_scope_pool_returns_open_forms_via_gsi3(self):
        repo = FormRepositoryMock()
        repo.forms.append(_pool_form())
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(user_id=INSPECTOR_ID, name="User", email="user@test.com", systems=["UBERLANDIA"])

        forms, next_key = usecase(requester=requester, limit=20, system=["UBERLANDIA"], scope="pool")

        assert [f.id for f in forms] == ['d61dbf66-a10f-11ed-a8fc-0242ac120040']
        assert next_key is None

    def test_scope_pool_requires_single_system(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo)
        requester = UserGatewayDTO(user_id=INSPECTOR_ID, name="User", email="user@test.com", systems=["UBERLANDIA", "GAIA"])

        with pytest.raises(EntityError):
            usecase(requester=requester, limit=20, scope="pool")

    def test_scope_all_requires_manager_role(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo, AccessControl(ProfileRepositoryMock(), SystemRoleRepositoryMock()))
        requester = UserGatewayDTO(user_id=INSPECTOR_ID, name="User", email="user@test.com", systems=["GAIA"])

        with pytest.raises(ForbiddenAction):
            usecase(requester=requester, limit=20, scope="all")

    def test_scope_all_with_forms_view_all_sees_every_form(self):
        repo = FormRepositoryMock()
        profile_repo, role_repo = ProfileRepositoryMock(), SystemRoleRepositoryMock()
        profile_repo.put_membership(SystemMembership(
            user_id=INSPECTOR_ID, system="GAIA", role_id="r-gestor-gaia", created_at=1, updated_at=1,
        ))
        usecase = GetAllFormsUsecase(repo, AccessControl(profile_repo, role_repo))
        requester = UserGatewayDTO(user_id=INSPECTOR_ID, name="User", email="user@test.com", systems=["GAIA"])

        forms, _ = usecase(requester=requester, limit=20, scope="all")

        assert len(forms) == len(repo.forms)

    def test_scope_all_needs_forms_view_all_in_every_requested_system(self):
        repo = FormRepositoryMock()
        profile_repo, role_repo = ProfileRepositoryMock(), SystemRoleRepositoryMock()
        profile_repo.put_membership(SystemMembership(
            user_id=INSPECTOR_ID, system="GAIA", role_id="r-gestor-gaia", created_at=1, updated_at=1,
        ))
        usecase = GetAllFormsUsecase(repo, AccessControl(profile_repo, role_repo))
        requester = UserGatewayDTO(
            user_id=INSPECTOR_ID, name="User", email="user@test.com", systems=["GAIA", "UBERLANDIA"],
        )

        with pytest.raises(ForbiddenAction):
            usecase(requester=requester, limit=20, scope="all")

    def test_scope_all_admin_sees_every_form_of_the_system(self):
        repo = FormRepositoryMock()
        usecase = GetAllFormsUsecase(repo, AccessControl(ProfileRepositoryMock(), SystemRoleRepositoryMock()))
        requester = UserGatewayDTO(user_id=ADMIN_ID, name="Admin", email="admin@test.com", systems=["GAIA"])

        forms, next_key = usecase(requester=requester, limit=20, scope="all")

        assert len(forms) == len(repo.forms)
