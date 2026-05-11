from pydantic import ValidationError

from .plan_route_usecase import PlanRouteUsecase
from .plan_route_viewmodel import PlanRouteViewmodel
from src.shared.helpers.contracts.runtime_requests import PlanRouteControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Forbidden, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class PlanRouteController:
    def __init__(self, usecase: PlanRouteUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = PlanRouteControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            ordered_forms, total_km = self.usecase(
                requester_user_id=requester_user.user_id,
                start_latitude=payload.start.latitude,
                start_longitude=payload.start.longitude,
                n=payload.n,
                end_latitude=payload.end.latitude if payload.end else None,
                end_longitude=payload.end.longitude if payload.end else None,
            )

            viewmodel = PlanRouteViewmodel(ordered_forms=ordered_forms, total_distance_km=total_km)
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
