from enum import Enum


class FormOrigin(Enum):
    """
    De onde partiu a demanda que virou uma OS (RN-009, especificação Uberlândia §8).
    Opcional — sistemas que não informam origem (ex.: Gaia) seguem sem ela.
    """

    CITIZEN = "CITIZEN"
    AI = "AI"
    FIELD = "FIELD"
    ORIGIN_SYSTEM = "ORIGIN_SYSTEM"
