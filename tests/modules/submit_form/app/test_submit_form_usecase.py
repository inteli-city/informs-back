import pytest
from src.modules.submit_form.app.submit_form_usecase import SubmitFormUsecase
from src.shared.domain.entities.field import FileField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.file_repository_mock import FileRepositoryMock


class TestSubmitFormUsecase:

    def test_submit_form_usecase(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"}
        ]

        usecase(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=form.id, fields=fields, completed_at=123)

        assert form.status == FormStatus.COMPLETED
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

        with pytest.raises(EntityError):
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
            file_type=FileType.IMAGE,
            min_quantity=1,
            max_quantity=1,
            value={"filename": "a.jpg", "mimetype": "image/jpeg", "size_bytes": 42, "checksum_sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="},
        )
        form.sections = [Section(section_id=1, fields=[file_field])]

        files = usecase(
            user_id=form.user_id,
            form_id=form.id,
            fields=[{"section_id": 1, "field_key": "file_key", "value": {"filename": "a.jpg", "mimetype": "image/jpeg", "size_bytes": 42, "checksum_sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="}}],
            completed_at=123,
        )

        assert len(files) == 1
        assert files[0].filename == "a.jpg"
        assert files[0].mimetype == "image/jpeg"
        assert files[0].size_bytes == 42
        assert files[0].checksum_sha256 == "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
        # value sempre lista após o upload, mesmo com 1 único arquivo
        # (consistência com o caso multi-arquivos para o consumidor downstream — Apex)
        value = form.sections[0].fields[0].value
        assert isinstance(value, list)
        assert len(value) == 1
        assert value[0].startswith("https://")
        assert form.sections[0].fields[0].file_integrity == [{
            "mimetype": "image/jpeg",
            "size_bytes": 42,
            "checksum_sha256": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        }]

    def test_rejeita_checksum_sha256_invalido(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)
        form = repo.forms[0]
        form.sections = [Section(section_id=1, fields=[FileField(
            placeholder='file', required=True, key='file_key', file_type=FileType.IMAGE,
            min_quantity=1, max_quantity=1,
        )])]

        with pytest.raises(EntityError):
            usecase(
                user_id=form.user_id,
                form_id=form.id,
                fields=[{"section_id": 1, "field_key": "file_key", "value": {
                    "filename": "a.jpg", "mimetype": "image/jpeg", "checksum_sha256": "invalido"
                }}],
                completed_at=123,
            )

    def test_submit_form_usecase_with_duplicated_section(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        file_field = FileField(
            placeholder='file',
            required=True,
            key='file_key',
            file_type=FileType.IMAGE,
            min_quantity=1,
            max_quantity=1,
        )
        form.sections = [Section(section_id=1, fields=[file_field], is_duplicable=True)]

        files = usecase(
            user_id=form.user_id,
            form_id=form.id,
            fields=[
                {"section_id": 1, "section_instance": 0, "field_key": "file_key", "value": {"filename": "a.jpg", "mimetype": "image/jpeg"}},
                {"section_id": 1, "section_instance": 1, "field_key": "file_key", "value": {"filename": "b.jpg", "mimetype": "image/jpeg"}},
            ],
            completed_at=123,
        )

        assert form.status == FormStatus.COMPLETED
        assert len(form.sections) == 2
        assert {s.section_instance for s in form.sections} == {0, 1}

        assert len(files) == 2
        by_instance = {f.section_instance: f for f in files}
        assert by_instance[0].filename == "a.jpg"
        assert by_instance[1].filename == "b.jpg"
        # o caminho no S3 separa as instâncias da seção
        assert '/sections/1/0/' in by_instance[0].file_path
        assert '/sections/1/1/' in by_instance[1].file_path

        # cada instância recebe as URLs dos seus próprios arquivos
        for section in form.sections:
            value = section.fields[0].value
            assert isinstance(value, list) and len(value) == 1
            assert value[0].startswith("https://")
        urls = [s.fields[0].value[0] for s in form.sections]
        assert urls[0] != urls[1]

    def test_submit_form_usecase_duplicated_section_not_duplicable(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        fields = [
            {"section_id": 1, "field_key": "key", "value": "poggers"},
            {"section_id": 1, "section_instance": 1, "field_key": "key", "value": "extra"},
        ]

        with pytest.raises(EntityError):
            usecase(user_id=form.user_id, form_id=form.id, fields=fields, completed_at=123)

    def test_submit_form_usecase_with_multiple_file_uploads(self):
        repo = FormRepositoryMock()
        file_repo = FileRepositoryMock()
        usecase = SubmitFormUsecase(repo, file_repo)

        form = repo.forms[0]

        file_field = FileField(
            placeholder='file',
            required=True,
            key='file_key',
            file_type=FileType.IMAGE,
            min_quantity=1,
            max_quantity=3,
            value=[
                {"filename": "a.jpg", "mimetype": "image/jpeg"},
                {"filename": "b.jpg", "mimetype": "image/jpeg"},
                {"filename": "c.jpg", "mimetype": "image/jpeg"},
            ],
        )
        form.sections = [Section(section_id=1, fields=[file_field])]

        files = usecase(
            user_id=form.user_id,
            form_id=form.id,
            fields=[{
                "section_id": 1,
                "field_key": "file_key",
                "value": [
                    {"filename": "a.jpg", "mimetype": "image/jpeg"},
                    {"filename": "b.jpg", "mimetype": "image/jpeg"},
                    {"filename": "c.jpg", "mimetype": "image/jpeg"},
                ],
            }],
            completed_at=123,
        )

        assert len(files) == 3
        value = form.sections[0].fields[0].value
        assert isinstance(value, list)
        assert len(value) == 3
        assert all(url.startswith("https://") for url in value)
