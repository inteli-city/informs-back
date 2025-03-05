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
        user_repo = Environments.get_user_repo()()

        groups = user_repo.get_groups_for_user(user_data['email'])

        if "FORMULARIOS" not in groups:
            raise ForbiddenAction('Usuário não esta apto para o sistema')
        
        groups.remove("FORMULARIOS")

        return UserGatewayDTO(
            user_id=user_data['sub'],
            name=user_data['name'],
            email=user_data['email'],
            systems=groups
        )
    
    def __eq__(self, other):
        return self.user_id == other.user_id