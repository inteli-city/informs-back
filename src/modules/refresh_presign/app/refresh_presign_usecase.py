from typing import Dict, List

from src.shared.domain.entities.file_upload import FileUpload
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.stored_file import StoredFile
from src.shared.domain.repositories.file_repository_interface import IFileRepository
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import NoItemsFound
from src.shared.helpers.functions.s3_url import extract_file_path


class RefreshPresignUsecase:
    """
    Re-assina a presigned URL de arquivos que o formulário já referencia.

    Existe porque a URL gerada no /submit tem validade curta: quando o upload
    do app falha e a retentativa acontece depois do prazo, sem este caso de uso
    a foto se torna inalcançável — o /submit não pode ser repetido (o formulário
    já não está IN_PROGRESS) e não havia outro caminho para obter URL nova.

    Regra central: só re-assina a key que já está gravada no formulário. Nunca
    gera key nova — isso deixaria órfão no bucket e faria a URL do DynamoDB
    apontar para um objeto que o app não vai enviar.
    """

    def __init__(self, form_repo: IFormRepository, file_repo: IFileRepository):
        self.form_repo = form_repo
        self.file_repo = file_repo

    def __call__(
        self,
        user_id: str,
        form_id: str,
        requested_files: List[dict],
    ) -> List[FileUpload]:
        form = self._get_form_or_raise(user_id=user_id, form_id=form_id)
        form.ensure_assigned_to(user_id, "Usuário não pode renovar arquivos de um formulário não direcionado a ele")

        stored_by_url = self._index_stored_files(form)

        return [
            self._refresh(stored_by_url, requested["file_url"], requested["mimetype"])
            for requested in requested_files
        ]

    def _get_form_or_raise(self, user_id: str, form_id: str) -> Form:
        form = self.form_repo.get_form_by_id(user_id=user_id, form_id=form_id)
        if form is None:
            raise NoItemsFound("Formulário não encontrado")
        return form

    @staticmethod
    def _index_stored_files(form: Form) -> Dict[str, StoredFile]:
        return {stored.file_url: stored for stored in form.stored_files()}

    def _refresh(self, stored_by_url: Dict[str, StoredFile], file_url: str, mimetype: str) -> FileUpload:
        stored = stored_by_url.get(file_url)
        if stored is None:
            # Não vaza se a URL existe em outro formulário: para este requester
            # ela simplesmente não é um arquivo válido.
            raise NoItemsFound("Arquivo não pertence a este formulário")

        file_path = extract_file_path(file_url)
        if file_path is None:
            raise EntityError("URL de arquivo não pertence ao bucket configurado")

        presigned_url = self.file_repo.generate_presigned_url(file_path=file_path, mimetype=mimetype)

        return FileUpload(
            filename=file_path.split("/")[-1],
            mimetype=mimetype,
            pre_signed_url=presigned_url,
            file_path=file_path,
            file_url=file_url,
            section_id=stored.section_id,
            section_instance=stored.section_instance,
            field_key=stored.field_key,
            file_index=stored.file_index,
        )
