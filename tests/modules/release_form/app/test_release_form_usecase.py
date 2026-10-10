import pytest

from src.modules.release_form.app.release_form_usecase import ReleaseFormUsecase
from src.shared.domain.entities.field import FileField, TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_event_repository_mock import FormEventRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock
from tests.modules.access_fixtures import give_role

ADMIN_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'   # seed do ProfileRepositoryMock
INSPECTOR_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120002'  # seed do ProfileRepositoryMock
OWNER_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120050'
FORM_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120031'

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _owned_form(**overrides) -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='preenchido')
    section = Section(section_id=1, fields=[text_field])
    base = dict(
        id=FORM_ID, form_title='FORM TITLE', created_by=OWNER_ID, user_id=OWNER_ID,
        system='UBERLANDIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.IN_PROGRESS, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )
    base.update(overrides)
    return Form(**base)


class TestReleaseFormUsecase:
    def setup_method(self):
        self.form_repo = FormRepositoryMock()
        self.file_repo = FileRepositoryMock()
        self.profile_repo = ProfileRepositoryMock()
        self.role_repo = SystemRoleRepositoryMock()
        self.form_event_repo = FormEventRepositoryMock()
        self.usecase = ReleaseFormUsecase(
            self.form_repo, self.file_repo, AccessControl(self.profile_repo, self.role_repo), self.form_event_repo,
        )

    def test_owner_releases_own_form(self):
        self.form_repo.forms.append(_owned_form())

        form = self.usecase(requester_user_id=OWNER_ID, requester_systems=['UBERLANDIA'], form_id=FORM_ID)

        assert form.user_id is None
        assert form.possession.value == 'OPEN'
        assert form.status == FormStatus.PENDING
        assert form.sections[0].fields[0].value is None
        assert len(self.form_event_repo.events) == 1
        assert self.form_event_repo.events[0].event_type.value == 'RELEASED'

    def test_admin_releases_form_of_another_user(self):
        self.form_repo.forms.append(_owned_form())

        form = self.usecase(requester_user_id=ADMIN_ID, requester_systems=None, form_id=FORM_ID)

        assert form.user_id is None

    def test_role_with_forms_release_releases_form_of_another_user(self):
        self.form_repo.forms.append(_owned_form())
        give_role(self.profile_repo, self.role_repo, INSPECTOR_ID, 'UBERLANDIA', [Action.FORMS_RELEASE])

        form = self.usecase(requester_user_id=INSPECTOR_ID, requester_systems=None, form_id=FORM_ID)

        assert form.user_id is None

    def test_non_owner_non_manager_raises_forbidden(self):
        self.form_repo.forms.append(_owned_form())

        with pytest.raises(ForbiddenAction):
            self.usecase(requester_user_id=INSPECTOR_ID, requester_systems=None, form_id=FORM_ID)

    def test_release_not_found_raises(self):
        with pytest.raises(NoItemsFound):
            self.usecase(requester_user_id=OWNER_ID, requester_systems=None, form_id='00000000-0000-0000-0000-000000000000')

    def test_release_deletes_stored_files_from_s3(self):
        file_field = FileField(label='fotos', required=False, key='fotos', order=1, file_type=FileType.IMAGE,
                                value="https://test.s3.sa-east-1.amazonaws.com/2026/UBERLANDIA/f1/a.jpg")
        section = Section(section_id=1, fields=[file_field])
        self.form_repo.forms.append(_owned_form(sections=[section]))

        self.usecase(requester_user_id=OWNER_ID, requester_systems=None, form_id=FORM_ID)

        assert "2026/UBERLANDIA/f1/a.jpg" in self.file_repo.deleted_file_paths

    def test_release_already_open_raises_forbidden(self):
        self.form_repo.forms.append(_owned_form(user_id=None, status=FormStatus.PENDING))

        with pytest.raises(ForbiddenAction):
            self.usecase(requester_user_id=ADMIN_ID, requester_systems=None, form_id=FORM_ID)
