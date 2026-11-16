from enum import Enum


class AssignmentOption(Enum):
    """
    Para quem a pessoa pode criar um formulário no app (seção "Para quem é o
    formulário"), ligado por role:

    - SELF: para ela mesma — o formulário nasce com ela como responsável.
    - TARGETED: para um grupo e/ou uma pessoa específica do sistema. Só grupo:
      fica no pool, visível só para quem é do grupo. Com pessoa: vai direto
      para ela.
    - OPEN: em aberto para o sistema todo. Também depende de o sistema permitir
      criação em aberto (`creation.allow_open`).
    """

    SELF = "self"
    TARGETED = "targeted"
    OPEN = "open"


# O que um role tem antes de alguém configurar: o comportamento de antes desta
# opção existir (para si; em aberto, se o sistema permitir).
DEFAULT_ASSIGNMENT_OPTIONS = (AssignmentOption.SELF, AssignmentOption.OPEN)
DEFAULT_ASSIGNMENT = AssignmentOption.SELF
