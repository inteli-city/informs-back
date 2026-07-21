from src.shared.helpers.errors.base_error import BaseError


class MissingParameters(BaseError):
    def __init__(self, message: str):
        super().__init__(f'Parâmetro ausente: {message}')


class WrongTypeParameter(BaseError):
    def __init__(self, field_name: str, field_type_expected: str, field_type_received: str):
        super().__init__(f'Campo {field_name} deveria ser do tipo {field_type_expected}, mas foi recebido um campo do tipo {field_type_received}')