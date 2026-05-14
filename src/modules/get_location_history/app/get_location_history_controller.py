from datetime import datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from .get_location_history_usecase import GetLocationHistoryUsecase
from .get_location_history_viewmodel import GetLocationHistoryViewmodel
from src.shared.helpers.contracts.runtime_requests import (
    GetLocationHistoryControllerRequestSchema,
)
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import (
    MissingParameters,
    WrongTypeParameter,
)
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import (
    IRequest,
    IResponse,
)
from src.shared.helpers.external_interfaces.http_codes import (
    BadRequest,
    Forbidden,
    NotFound,
    OK,
)
from src.shared.helpers.functions.pydantic_error_parser import (
    get_validation_error_message,
)
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


# Operação acontece no Brasil — "rota do dia" pro admin é o dia
# operacional em São Paulo, não o dia UTC. Hardcoded propositalmente
# (toda a base de inspectors está em território nacional).
_OPERATION_TZ = ZoneInfo("America/Sao_Paulo")


def _default_since_ms() -> int:
    """00:00 do dia atual em America/Sao_Paulo, em epoch ms UTC."""
    now_local = datetime.now(_OPERATION_TZ)
    midnight_local = datetime.combine(now_local.date(), time.min, tzinfo=_OPERATION_TZ)
    return int(midnight_local.timestamp() * 1000)


def _default_until_ms() -> int:
    """Agora, em epoch ms UTC."""
    return int(datetime.now(timezone.utc).timestamp() * 1000)


class GetLocationHistoryController:
    def __init__(self, usecase: GetLocationHistoryUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetLocationHistoryControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(
                payload.requester_user.model_dump(by_alias=True)
            )

            since_ms = payload.since if payload.since is not None else _default_since_ms()
            until_ms = payload.until if payload.until is not None else _default_until_ms()

            pings = self.usecase(
                requester_user_id=requester_user.user_id,
                target_user_id=payload.user_id,
                since_ms=since_ms,
                until_ms=until_ms,
            )

            viewmodel = GetLocationHistoryViewmodel(pings=pings)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except MissingParameters as err:
            return BadRequest(body=err.message)
        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
