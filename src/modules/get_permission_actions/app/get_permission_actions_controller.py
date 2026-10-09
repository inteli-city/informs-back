from .get_permission_actions_usecase import GetPermissionActionsUsecase
from .get_permission_actions_viewmodel import GetPermissionActionsViewmodel
from src.shared.helpers.contracts.runtime_requests import GetPermissionActionsControllerRequestSchema
from src.shared.helpers.access_error_response import HANDLED_ERRORS, access_error_response
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK


class GetPermissionActionsController:
    def __init__(self, usecase: GetPermissionActionsUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            # Só confere que veio de um usuário autenticado; o catálogo é o mesmo para todos.
            GetPermissionActionsControllerRequestSchema.model_validate(data)
            result = self.usecase()

            viewmodel = GetPermissionActionsViewmodel(result)
            return OK(viewmodel.to_dict())

        except HANDLED_ERRORS as err:
            return access_error_response(err)
