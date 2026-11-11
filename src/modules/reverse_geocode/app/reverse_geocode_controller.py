from pydantic import ValidationError

from .reverse_geocode_usecase import ReverseGeocodeUsecase
from .reverse_geocode_viewmodel import ReverseGeocodeViewmodel
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.contracts.runtime_requests import ReverseGeocodeControllerRequestSchema
from src.shared.helpers.errors.usecase_errors import NoItemsFound, ReverseGeocodeUnavailable
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadGateway, BadRequest, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message


class ReverseGeocodeController:
    def __init__(self, usecase: ReverseGeocodeUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = ReverseGeocodeControllerRequestSchema.model_validate(data)

            address = self.usecase(latitude=payload.lat, longitude=payload.lng)

            return OK(ReverseGeocodeViewmodel(address).to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))
        except NoItemsFound as err:
            return NotFound(body=err.message)
        except ReverseGeocodeUnavailable as err:
            return BadGateway(body=err.message)
