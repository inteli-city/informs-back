from typing import List, Optional

from .create_template_usecase import CreateTemplateUsecase
from .create_template_viewmodel import TemplateViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Created, InternalServerError
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateTemplateController:
    def __init__(self, usecase: CreateTemplateUsecase):
        self.usecase = usecase

    def _validate_and_extract_parameters(self, body: dict) -> tuple:
        name = body.get("name")
        system = body.get("system")
        description: Optional[str] = body.get("description")
        is_active = body.get("isActive")
        sessions_raw = body.get("sessions")

        if name is None:
            raise MissingParameters("name")
        if system is None:
            raise MissingParameters("system")
        if is_active is None:
            raise MissingParameters("isActive")
        if sessions_raw is None:
            raise MissingParameters("sessions")

        if not isinstance(name, str):
            raise WrongTypeParameter("name", "str", type(name))
        if not isinstance(system, str):
            raise WrongTypeParameter("system", "str", type(system))
        if description is not None and not isinstance(description, str):
            raise WrongTypeParameter("description", "str", type(description))
        if not isinstance(is_active, bool):
            raise WrongTypeParameter("isActive", "bool", type(is_active))
        if not isinstance(sessions_raw, list):
            raise WrongTypeParameter("sessions", "list", type(sessions_raw))

        return name, system, description, is_active, sessions_raw

    def __call__(self, request: IRequest) -> IResponse:
        try:
            requester_user = request.data.get("requester_user")
            if requester_user is None:
                raise MissingParameters("requester_user")
            requester = UserGatewayDTO.from_api_gateway(requester_user)

            body = request.data if isinstance(request.data, dict) else {}
            name, system, description, is_active, sessions_raw = self._validate_and_extract_parameters(body)

            sessions = [SectionDTO.from_request(session).to_entity() for session in sessions_raw]

            template = self.usecase(
                creator_user_id=requester.user_id,
                name=name,
                system=system,
                description=description,
                is_active=is_active,
                sessions=sessions,
            )

            viewmodel = TemplateViewmodel(template)
            return Created(viewmodel.to_dict())

        except MissingParameters as err:
            return BadRequest(err.message)
        except WrongTypeParameter as err:
            return BadRequest(err.message)
        except EntityError as err:
            return BadRequest(f"Parâmetro inválido: {err.message}")
        except DuplicatedItem as err:
            return Conflict(err.message)
        except Exception as err:
            return InternalServerError(err.args[0] if err.args else str(err))
