from typing import Optional

from src.modules.update_template.app.update_template_viewmodel import TemplateViewmodel
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, InternalServerError, NotFound, OK
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateTemplateController:
    def __init__(self, usecase: UpdateTemplateUsecase):
        self.usecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            requester_user = request.data.get("requester_user")
            if requester_user is None:
                raise MissingParameters("requester_user")
            requester = UserGatewayDTO.from_api_gateway(requester_user)

            template_id = request.data.get("template_id") or request.data.get("templateId")
            if template_id is None:
                raise MissingParameters("template_id")

            body = request.data if isinstance(request.data, dict) else {}
            name: Optional[str] = body.get("name")
            system: Optional[str] = body.get("system")
            description: Optional[str] = body.get("description")
            is_active = body.get("isActive")
            sessions_raw = body.get("sessions")

            if name is not None and not isinstance(name, str):
                raise WrongTypeParameter("name", "str", type(name))
            if system is not None and not isinstance(system, str):
                raise WrongTypeParameter("system", "str", type(system))
            if description is not None and not isinstance(description, str):
                raise WrongTypeParameter("description", "str", type(description))
            if is_active is not None and not isinstance(is_active, bool):
                raise WrongTypeParameter("isActive", "bool", type(is_active))
            if sessions_raw is not None and not isinstance(sessions_raw, list):
                raise WrongTypeParameter("sessions", "list", type(sessions_raw))

            sessions = [SectionDTO.from_request(session).to_entity() for session in sessions_raw] if sessions_raw is not None else None

            updated_template = self.usecase(
                template_id=template_id,
                requester_user_id=requester.user_id,
                name=name,
                system=system,
                description=description,
                is_active=is_active,
                sessions=sessions,
            )

            viewmodel = TemplateViewmodel(updated_template)
            return OK(viewmodel.to_dict())

        except MissingParameters as err:
            return BadRequest(err.message)
        except WrongTypeParameter as err:
            return BadRequest(err.message)
        except EntityError as err:
            return BadRequest(f"Parâmetro inválido: {err.message}")
        except NoItemsFound as err:
            return NotFound(err.message)
        except DuplicatedItem as err:
            return Conflict(err.message)
        except Exception as err:
            return InternalServerError(err.args[0] if err.args else str(err))
