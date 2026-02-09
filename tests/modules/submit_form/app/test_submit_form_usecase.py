import pytest
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock


class Test_SubmitFormUsecase:

    def test_submit_form_usecase(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        usecase(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=form.id, fields=fields, completed_at=123)

        assert form.status == FORM_STATUS.COMPLETED
        assert form.sections[0].fields[0].value == 'poggers'
        assert form.completed_at == 123
    
    def test_submit_form_usecase_user_disabled(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[1]
        
        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.id, fields, completed_at=123)

    def test_submit_form_usecase_form_not_found(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        
        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        with pytest.raises(NoItemsFound):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', '123', fields, completed_at=123)
    
    def test_submit_form_usecase_user_not_owner(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]
        
        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120002', form.id, fields, completed_at=123)
    
    def test_submit_form_usecase_form_already_concluded(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[1]
        
        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.id, fields, completed_at=123)
    
    def test_submit_form_usecase_required_field_not_filled(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]
        
        fields = [
            {"section_id": 1, "field_key": "key", "value": None}
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.id, fields, completed_at=123)

    def test_submit_form_usecase_with_file_uploads(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        file_field = FileField(
            placeholder='file',
            required=True,
            key='file_key',
            file_type=FILE_TYPE.IMAGE,
            min_quantity=1,
            max_quantity=1,
            value={"filename": "a.jpg", "mimetype": "image/jpeg"},
        )
        form.sections = [Section(section_id=1, fields=[file_field])]

        files = usecase(
            user_id=form.user_id,
            form_id=form.id,
            fields=[{"section_id": 1, "field_key": "file_key", "value": {"filename": "a.jpg", "mimetype": "image/jpeg"}}],
            completed_at=123,
        )

        assert len(files) == 1
        assert files[0].filename == "a.jpg"
        assert files[0].mimetype == "image/jpeg"
        assert form.sections[0].fields[0].value.startswith("https://")
