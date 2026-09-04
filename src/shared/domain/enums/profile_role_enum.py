from enum import Enum


class ProfileRole(Enum):
    """
    RBAC do Informs (independente do Cognito).

    - ADMIN: pode gerenciar perfis (criar, deletar). Por padrão, também tem
      acesso operacional aos formulários como qualquer outro usuário.
    - INSPECTOR: usuário de campo (ex.: motoverificador) que recebe e
      preenche formulários. Não pode gerenciar perfis.
    - MANAGER (Gestor) / SUPERVISOR (Fiscal): papéis do contrato de
      Uberlândia (SGISV). Em V01 têm as mesmas capacidades operacionais de
      INSPECTOR mais reatribuição/geração de OS em campo — a distinção
      entre os dois só aparece em uma versão futura. RBAC de fato é
      construído na Fase 2 da integração; por ora só os valores existem.

    O Cognito segue como o IdP (autenticação + grupo FORMULARIOS), e este
    enum vive no DynamoDB para controlar autorização interna do produto.
    """

    ADMIN = "ADMIN"
    INSPECTOR = "INSPECTOR"
    MANAGER = "MANAGER"
    SUPERVISOR = "SUPERVISOR"
