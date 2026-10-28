from dataclasses import dataclass
from typing import Optional

from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.possession_enum import Possession


@dataclass(frozen=True)
class TemplateFormSummary:
    """
    Um formulário visto a partir do template de que ele nasceu: só o que a tela
    de propagação de versão precisa para a pessoa escolher quais atualizar.

    É o que o índice do template (`TemplateIndex`) projeta — sem seções, que
    num pool de milhares de OS fariam a lista pesar dezenas de MB.
    """

    id: str
    form_title: str
    system: str
    status: FormStatus
    possession: Possession
    created_at: int
    template_version: int
    user_id: Optional[str] = None
    street: Optional[str] = None
    number: Optional[int] = None
    city: Optional[str] = None

    def is_open(self) -> bool:
        """Pendente ou em execução: o que pode receber uma nova versão."""
        return self.status in (FormStatus.PENDING, FormStatus.IN_PROGRESS)
