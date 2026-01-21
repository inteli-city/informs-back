import pytest
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.shared.domain.entities.field import FileField, TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock
from src.shared.infra.repositories.queue_repository_mock import QueueRepositoryMock


class Test_SubmitFormUsecase:

    def test_submit_form_usecase(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        usecase(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=form.form_id, sections=sections, completed_at=123)

        assert form.status == FORM_STATUS.COMPLETED
        assert form.sections[0].fields[0].value == 'poggers'
        assert form.completed_at == 123
        assert len(queue_repo.messages) == 1
    
    def test_submit_form_usecase_user_disabled(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        form = repo.forms[1]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections, completed_at=123)

    def test_submit_form_usecase_form_not_found(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        with pytest.raises(NoItemsFound):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', '123', sections, completed_at=123)
    
    def test_submit_form_usecase_user_not_owner(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120002', form.form_id, sections, completed_at=123)
    
    def test_submit_form_usecase_form_already_concluded(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        form = repo.forms[1]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections, completed_at=123)
    
    def test_submit_form_usecase_required_field_not_filled(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value=None)

        sections = [
            Section(
                section_id=1,
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections, completed_at=123)

    def test_submit_form_usecase_with_file_uploads(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        queue_repo = QueueRepositoryMock()
        usecase = SubmitFormUsecase(repo, image_repo, queue_repo)

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
        sections = [
            Section(
                section_id=1,
                fields=[file_field]
            )
        ]

        images = usecase(
            user_id=form.user_id,
            form_id=form.form_id,
            sections=sections,
            completed_at=123,
            file_uploads={(1, "file_key"): [{"filename": "a.jpg", "mimetype": "image/jpeg"}]},
        )

        assert len(images) == 1
        assert images[0].filename == "a.jpg"
        assert images[0].mimetype == "image/jpeg"
        assert form.sections[0].fields[0].value.startswith("https://")
