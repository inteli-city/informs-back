from src.modules.release_form.app.release_form_controller import ReleaseFormController
from src.modules.release_form.app.release_form_usecase import ReleaseFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_event_repository_mock import FormEventRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock

INSPECTOR_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120002'  # seed do ProfileRepositoryMock
OWNER_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120050'
FORM_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120031'

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _owned_form() -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='preenchido')
    section = Section(section_id=1, fields=[text_field])
    return Form(
        id=FORM_ID, form_title='FORM TITLE', created_by=OWNER_ID, user_id=OWNER_ID,
        system='UBERLANDIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.IN_PROGRESS, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )


def _request(form_id: str, sub: str, groups: str = "FORMULARIOS,UBERLANDIA"):
    return HttpRequest(body={
        "requester_user": {"sub": sub, "name": "Tester", "email": "tester@example.com", "cognito:groups": groups},
        "form_id": form_id,
    })


class TestReleaseFormController:
    def setup_method(self):
        self.form_repo = FormRepositoryMock()
        self.form_repo.forms.append(_owned_form())
        self.controller = ReleaseFormController(ReleaseFormUsecase(
            self.form_repo, FileRepositoryMock(), AccessControl(ProfileRepositoryMock(), SystemRoleRepositoryMock()),
            FormEventRepositoryMock(),
        ))

    def test_owner_release_success_returns_200(self):
        response = self.controller(_request(FORM_ID, sub=OWNER_ID))
        assert response.status_code == 200
        assert response.body["user_id"] is None
        assert response.body["possession"] == "OPEN"

    def test_non_owner_non_manager_returns_403(self):
        response = self.controller(_request(FORM_ID, sub=INSPECTOR_ID))
        assert response.status_code == 403

    def test_release_not_found_returns_404(self):
        response = self.controller(_request("00000000-0000-0000-0000-000000000000", sub=OWNER_ID))
        assert response.status_code == 404
