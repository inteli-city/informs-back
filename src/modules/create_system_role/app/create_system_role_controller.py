from .create_system_role_usecase import CreateSystemRoleUsecase
from .create_system_role_viewmodel import CreateSystemRoleViewmodel
from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.contracts.runtime_requests import CreateSystemRoleControllerRequestSchema
from src.shared.helpers.access_error_response import HANDLED_ERRORS, access_error_response
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import Created
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateSystemRoleController:
    def __init__(self, usecase: CreateSystemRoleUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = CreateSystemRoleControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(
                requester_user_id=requester_user.user_id,
                system=payload.system,
                name=payload.name,
                actions=[Action(value) for value in payload.actions],
                is_default=payload.is_default,
            )

            viewmodel = CreateSystemRoleViewmodel(result)
            return Created(viewmodel.to_dict())

        except HANDLED_ERRORS as err:
            return access_error_response(err)
