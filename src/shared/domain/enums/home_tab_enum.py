from enum import Enum


class HomeTab(Enum):
    """
    Aba em que o app abre para quem tem o role: criar formulário, lista de
    formulários ou mapa. Quem não tem role no sistema (ou tem o ADMIN, que é
    fixo) abre na lista.
    """

    CREATE = "create"
    LIST = "list"
    MAP = "map"
