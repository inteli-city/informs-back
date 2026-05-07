from functools import wraps
from typing import Any, Callable, TypeVar, cast

from src.shared.helpers.external_interfaces.http_codes import InternalServerError
from src.shared.helpers.functions.exception_message import get_exception_message

F = TypeVar("F", bound=Callable[..., Any])


def controller_error_handler(fn: F) -> F:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception as err:
            return InternalServerError(body=get_exception_message(err))

    return cast(F, wrapper)
