import pytest

from src.modules.assign_form.app.assign_form_usecase import AssignFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_event_repository_mock import FormEventRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock

ADMIN_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'   # seed do ProfileRepositoryMock
INSPECTOR_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120002'  # seed do ProfileRepositoryMock
TARGET_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120060'
POOL_FORM_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120032'


def _give_role(profile_repo, role_repo, user_id, system, actions):
    """Cria no sistema um role com as ações e dá à pessoa."""
    role = role_repo.put_role(SystemRole(
        system=system, role_id=f"r-{system.lower()}", name="Gestor", actions=actions, created_at=1, updated_at=1,
    ))
    profile_repo.put_membership(SystemMembership(
        user_id=user_id, system=system, role_id=role.role_id, created_at=1, updated_at=1,
    ))

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _pool_form(**overrides) -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    section = Section(section_id=1, fields=[text_field])
    base = dict(
        id=POOL_FORM_ID, form_title='FORM TITLE', created_by=ADMIN_ID, user_id=None,
        system='UBERLANDIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )
    base.update(overrides)
    return Form(**base)


class TestAssignFormUsecase:
    def setup_method(self):
        self.form_repo = FormRepositoryMock()
        self.profile_repo = ProfileRepositoryMock()
        self.role_repo = SystemRoleRepositoryMock()
        self.form_event_repo = FormEventRepositoryMock()
        self.usecase = AssignFormUsecase(
            self.form_repo, AccessControl(self.profile_repo, self.role_repo), self.form_event_repo,
        )

    def test_admin_assigns_pool_form_to_target(self):
        self.form_repo.forms.append(_pool_form())

        form = self.usecase(
            requester_user_id=ADMIN_ID, requester_systems=None, form_id=POOL_FORM_ID, target_user_id=TARGET_ID,
        )

        assert form.user_id == TARGET_ID
        assert form.assignment_source.value == 'MANAGER'
        assert len(self.form_event_repo.events) == 1
        assert self.form_event_repo.events[0].event_type.value == 'ASSIGNED'
        assert self.form_event_repo.events[0].target_user_id == TARGET_ID

    def test_role_with_forms_assign_in_the_form_system_assigns(self):
        self.form_repo.forms.append(_pool_form())
        _give_role(self.profile_repo, self.role_repo, INSPECTOR_ID, 'UBERLANDIA', [Action.FORMS_ASSIGN])

        form = self.usecase(
            requester_user_id=INSPECTOR_ID, requester_systems=None, form_id=POOL_FORM_ID, target_user_id=TARGET_ID,
        )

        assert form.user_id == TARGET_ID

    def test_forms_assign_in_another_system_is_forbidden(self):
        self.form_repo.forms.append(_pool_form())
        _give_role(self.profile_repo, self.role_repo, INSPECTOR_ID, 'GAIA', [Action.FORMS_ASSIGN])

        with pytest.raises(ForbiddenAction):
            self.usecase(
                requester_user_id=INSPECTOR_ID, requester_systems=None, form_id=POOL_FORM_ID, target_user_id=TARGET_ID,
            )

    def test_inspector_cannot_assign_raises_forbidden(self):
        self.form_repo.forms.append(_pool_form())

        with pytest.raises(ForbiddenAction):
            self.usecase(
                requester_user_id=INSPECTOR_ID, requester_systems=None, form_id=POOL_FORM_ID, target_user_id=TARGET_ID,
            )

    def test_assign_not_found_raises(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                requester_user_id=ADMIN_ID, requester_systems=None,
                form_id='00000000-0000-0000-0000-000000000000', target_user_id=TARGET_ID,
            )

    def test_assign_already_owned_raises_conflict(self):
        self.form_repo.forms.append(_pool_form(user_id=TARGET_ID))

        with pytest.raises(DuplicatedItem):
            self.usecase(
                requester_user_id=ADMIN_ID, requester_systems=None, form_id=POOL_FORM_ID, target_user_id=TARGET_ID,
            )
