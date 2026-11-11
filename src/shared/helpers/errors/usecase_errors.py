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


class TemplateVersionRequired(BaseError):
    """O template já tem formulários e o pedido muda o que eles copiam
    (seções, motivos): só entra como nova versão (`new_version`)."""
    def __init__(self):
        super().__init__(
            'Este template já tem formulários. Para alterar seções, campos ou motivos de '
            'cancelamento, crie uma nova versão.'
        )


class ReverseGeocodeUnavailable(BaseError):
    """O serviço de endereço (revgeo) não respondeu como esperado. Não é erro
    de quem pediu: o app avisa e a pessoa preenche o endereço à mão."""
    def __init__(self, message: str = 'Serviço de endereço indisponível'):
        super().__init__(message)
