from typing import List

from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import ForbiddenAction

class UserGatewayDTO:
    user_id: str
    name: str
    email: str
    systems: List[str]

    def __init__(self, user_id: str, name: str, email: str, systems: List[str]):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.systems = systems

    @staticmethod
    def from_api_gateway(user_data: dict) -> 'UserGatewayDTO':
        """
        This method is used to convert the user data from the API Gateway to a UserApiGatewayDTO object.
        """

        systems = [item.strip() for item in user_data['cognito:groups'].split(",")]

        if "FORMULARIOS" not in systems:
            raise ForbiddenAction('Usuário não esta apto para o sistema')
        
        systems.remove("FORMULARIOS")

        return UserGatewayDTO(
            user_id=user_data['sub'],
            name=user_data['name'],
            email=user_data['email'],
            systems=systems
        )
    
    def __eq__(self, other):
        return self.user_id == other.user_id