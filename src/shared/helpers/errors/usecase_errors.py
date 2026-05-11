from typing import List

from src.shared.helpers.errors.base_error import BaseError

class NoItemsFound(BaseError):
    def __init__(self, message: str):
        super().__init__(message)


class FormsNotFound(NoItemsFound):
    """
    Subtipo de NoItemsFound usado quando o cliente passa uma lista explícita de
    form_ids e algum não existe ou não pertence ao requester. Carrega a lista
    dos IDs faltantes para o controller responder com 404 detalhado.
    """

    def __init__(self, missing_form_ids: List[str]):
        self.missing_form_ids = list(missing_form_ids)
        joined = ", ".join(self.missing_form_ids)
        super().__init__(f"Formulários não encontrados ou inacessíveis: {joined}")


class DuplicatedItem(BaseError):
    def __init__(self, message: str):
        super().__init__(message)
        
class ForbiddenAction(BaseError):
    def __init__(self, message: str):
        super().__init__(f'Ação não permitida: {message}')

class ErrorWithFile(BaseError):
    def __init__(self, message: str):
        super().__init__(f'Erro salvando arquivo: {message}')


class InvalidPaginationToken(BaseError):
    def __init__(self):
        super().__init__('Parâmetro de paginação inválido')
