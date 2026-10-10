from pydantic import ValidationError

from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Forbidden, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message


# Erros esperados das rotas de acesso por sistema (/systems, /permissions).
# O que não está aqui cai no controller_error_handler (500).
HANDLED_ERRORS = (
    ValidationError, NoItemsFound, DuplicatedItem, MissingParameters, ForbiddenAction, WrongTypeParameter, EntityError,
)


def access_error_response(err: Exception) -> IResponse:
    """Status HTTP de cada erro esperado — o mesmo mapeamento dos demais controllers."""
    if isinstance(err, ValidationError):
        return BadRequest(body=get_validation_error_message(err))
    if isinstance(err, NoItemsFound):
        return NotFound(body=err.message)
    if isinstance(err, DuplicatedItem):
        return Conflict(body=err.message)
    if isinstance(err, ForbiddenAction):
        return Forbidden(body=err.message)
    if isinstance(err, EntityError):
        return BadRequest(body=f"Parâmetro inválido: {err.message}")
    return BadRequest(body=err.message)
