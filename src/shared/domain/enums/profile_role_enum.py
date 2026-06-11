from enum import Enum


class ProfileRole(Enum):
    """
    RBAC do Informs (independente do Cognito).

    - ADMIN: pode gerenciar perfis (criar, deletar). Por padrão, também tem
      acesso operacional aos formulários como qualquer outro usuário.
    - INSPECTOR: usuário de campo (ex.: motoverificador) que recebe e
      preenche formulários. Não pode gerenciar perfis.

    O Cognito segue como o IdP (autenticação + grupo FORMULARIOS), e este
    enum vive no DynamoDB para controlar autorização interna do produto.
    """

    ADMIN = "ADMIN"
    INSPECTOR = "INSPECTOR"
