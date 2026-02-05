from src.shared.helpers.errors.base_error import BaseError

class NoItemsFound(BaseError):
    def __init__(self, message: str):
        super().__init__(message)

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
