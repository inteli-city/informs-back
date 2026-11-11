import os
import sys

sys.path.append(os.getcwd())

from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.modules.create_template.app.create_template_controller import CreateTemplateController
from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock

USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
USER = {"sub": USER_ID, "name": "User", "email": "user@test.com", "cognito:groups": "FORMULARIOS,GAIA"}
SECTION = {"section_id": 1, "fields": [{"field_type": "TEXT_FIELD", "label": "Nome", "required": True, "key": "nome", "order": 0}]}
REQUIREMENT = {
    "key": "foto_evidencia", "label": "Foto de evidência",
    "information_field_type": "FILE_INFORMATION_FIELD", "required": True, "file_type": "IMAGE",
}


def _template_body(information_fields):
    return {
        "requester_user": USER, "name": "T", "system": "GAIA", "is_active": True,
        "sections": [SECTION], "information_fields": information_fields,
    }


def _form_body(template_id, information_fields):
    return {
        "requester_user": USER, "form_title": "F", "user_id": USER_ID, "system": "GAIA", "street": "1", "city": "1",
        "latitude": 1.0, "longitude": 1.0, "priority": 3, "template": template_id,
        "justifications": [{"option": "o", "required_image": False, "required_text": False}],
        "information_fields": information_fields,
    }


def _stack():
    templates = TemplateRepositoryMock()
    create_template = CreateTemplateController(CreateTemplateUsecase(templates))
    create_form = CreateFormController(CreateFormUsecase(FormRepositoryMock(), FileRepositoryMock(), template_repo=templates))
    return create_template, create_form


def test_template_with_requirement_to_form_over_http_contract():
    create_template, create_form = _stack()
    created = create_template(HttpRequest(body=_template_body([REQUIREMENT])))
    assert created.status_code == 201
    assert created.body["information_fields"] == [REQUIREMENT]

    template_id = created.body["id"]
    # sem a foto exigida: recusa
    missing = create_form(HttpRequest(body=_form_body(template_id, [])))
    assert missing.status_code == 400 and "obrigatório" in missing.body

    photo = {"key": "foto_evidencia", "information_field_type": "FILE_INFORMATION_FIELD",
             "filename": "e.jpg", "mimetype": "image/jpeg", "file_type": "IMAGE"}
    # categoria errada: recusa
    pdf = {**photo, "filename": "e.pdf", "mimetype": "application/pdf"}
    wrong = create_form(HttpRequest(body=_form_body(template_id, [pdf])))
    assert wrong.status_code == 400 and "Tipo de arquivo" in wrong.body

    ok = create_form(HttpRequest(body=_form_body(template_id, [photo])))
    assert ok.status_code == 201
    assert ok.body["information_fields"][0]["key"] == "foto_evidencia"


def test_template_contract_rejects_file_type_on_text_and_repeated_keys():
    create_template, _ = _stack()
    bad_type = {**REQUIREMENT, "information_field_type": "TEXT_INFORMATION_FIELD"}
    assert create_template(HttpRequest(body=_template_body([bad_type]))).status_code == 400
    assert create_template(HttpRequest(body=_template_body([REQUIREMENT, REQUIREMENT]))).status_code == 400


def test_template_without_information_fields_keeps_working():
    create_template, create_form = _stack()
    body = _template_body(None)
    created = create_template(HttpRequest(body=body))
    assert created.status_code == 201 and created.body["information_fields"] == []
    assert create_form(HttpRequest(body=_form_body(created.body["id"], []))).status_code == 201


def test_form_responses_return_the_template_id():
    from src.modules.get_form.app.get_form_controller import GetFormController
    from src.modules.get_form.app.get_form_usecase import GetFormUsecase

    templates = TemplateRepositoryMock()
    forms = FormRepositoryMock()
    create_template = CreateTemplateController(CreateTemplateUsecase(templates))
    create_form = CreateFormController(CreateFormUsecase(forms, FileRepositoryMock(), template_repo=templates))
    template_id = create_template(HttpRequest(body=_template_body(None))).body["id"]

    created = create_form(HttpRequest(body=_form_body(template_id, [])))
    assert created.status_code == 201 and created.body["template"] == template_id

    got = GetFormController(GetFormUsecase(forms))(
        HttpRequest(body={"requester_user": USER, "form_id": created.body["id"]}))
    assert got.status_code == 200 and got.body["template"] == template_id
