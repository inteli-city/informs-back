from src.modules.assign_form.app.assign_form_controller import AssignFormController
from src.modules.assign_form.app.assign_form_usecase import AssignFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_event_repository_mock import FormEventRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock

ADMIN_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'   # seed do ProfileRepositoryMock
INSPECTOR_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120002'  # seed do ProfileRepositoryMock
TARGET_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120060'
POOL_FORM_ID = 'd61dbf66-a10f-11ed-a8fc-0242ac120032'

justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image'),
)


def _pool_form() -> Form:
    text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
    section = Section(section_id=1, fields=[text_field])
    return Form(
        id=POOL_FORM_ID, form_title='FORM TITLE', created_by=ADMIN_ID, user_id=None,
        system='UBERLANDIA', street='1', city='1', latitude=1.0, longitude=1.0,
        priority=Priority.EMERGENCY, status=FormStatus.PENDING, created_at=1, updated_at=1,
        justification=justification, sections=[section],
    )


def _request(form_id: str, sub: str, target_user_id: str = TARGET_ID, groups: str = "FORMULARIOS,UBERLANDIA"):
    return HttpRequest(body={
        "requester_user": {"sub": sub, "name": "Tester", "email": "tester@example.com", "cognito:groups": groups},
        "form_id": form_id,
        "user_id": target_user_id,
    })


class TestAssignFormController:
    def setup_method(self):
        self.form_repo = FormRepositoryMock()
        self.form_repo.forms.append(_pool_form())
        self.controller = AssignFormController(AssignFormUsecase(
            self.form_repo, AccessControl(ProfileRepositoryMock(), SystemRoleRepositoryMock()), FormEventRepositoryMock(),
        ))

    def test_admin_assign_success_returns_200(self):
        response = self.controller(_request(POOL_FORM_ID, sub=ADMIN_ID))
        assert response.status_code == 200
        assert response.body["user_id"] == TARGET_ID

    def test_inspector_cannot_assign_returns_403(self):
        response = self.controller(_request(POOL_FORM_ID, sub=INSPECTOR_ID))
        assert response.status_code == 403

    def test_assign_missing_user_id_returns_400(self):
        request = HttpRequest(body={
            "requester_user": {"sub": ADMIN_ID, "name": "Tester", "email": "tester@example.com", "cognito:groups": "FORMULARIOS"},
            "form_id": POOL_FORM_ID,
        })
        response = self.controller(request)
        assert response.status_code == 400
