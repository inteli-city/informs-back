from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.template_form_summary import TemplateFormSummary
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.assignment_source_enum import AssignmentSource
from src.shared.domain.enums.form_status_enum import FormStatus


class IFormRepository(ABC):

    @abstractmethod
    def get_form_by_id(self, user_id: str, form_id: str) -> Optional[Form]:
        pass
    
    @abstractmethod
    def get_form_by_user_id(self, user_id: str) -> List[Form]:
        pass

    @abstractmethod
    def get_all_forms(
        self,
        limit: Optional[int],
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
        system: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        updated_at_start: Optional[int] = None,
        updated_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        pass

    @abstractmethod
    def get_forms_updated_since(
        self,
        system: str,
        updated_at_start: int,
        updated_at_end: Optional[int] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        pass

    @abstractmethod
    def get_form_by_external_id(self, system: str, external_id: str) -> Optional[Form]:
        pass

    @abstractmethod
    def create_form(self, form: Form) -> Form:
        pass

    @abstractmethod
    def update_form(
        self,
        user_id: str,
        form_id: str,
        status: Optional[FormStatus] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        sections: Optional[List[Section]] = None,
        justification: Optional[Justification] = None,
        expected_status: Optional[FormStatus] = None,
        completed_by: Optional[str] = None,
    ) -> Optional[Form]:
        pass

    @abstractmethod
    def claim_form(
        self,
        form_id: str,
        user_id: str,
        claimed_at: int,
        updated_at: int,
        source: AssignmentSource = AssignmentSource.CLAIM,
    ) -> Optional[Form]:
        """Reivindica (ou atribui, com `source=MANAGER`) uma OS do pool de forma
        atômica e exclusiva (RN-UBE-002) — `None` se a OS não existe;
        levanta `DuplicatedItem` se já tiver dono."""
        pass

    @abstractmethod
    def release_form(self, form_id: str, sections: List[Section], released_at: int, updated_at: int) -> Optional[Form]:
        """Devolve ao pool com método dedicado (decisão P12) — `REMOVE` de
        `user_id`/GSI1PK/GSI1SK/in_progress_at, não `SET ... = null`."""
        pass

    @abstractmethod
    def get_pool_forms(
        self,
        system: str,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        """OS abertas no pool de um `system`, via GSI3 esparso (§14.1) —
        nunca cai em Scan."""
        pass

    @abstractmethod
    def has_forms_with_template(self, template_id: str) -> bool:
        """Algum formulário (de qualquer status) nasceu deste template? Decide
        se o template ainda pode ser editado sem criar uma nova versão."""
        pass

    @abstractmethod
    def get_forms_by_template(
        self,
        template_id: str,
        only_open: bool = True,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
    ) -> Tuple[List[TemplateFormSummary], Optional[str]]:
        """Formulários de um template, pelo `TemplateIndex`, em resumo (sem
        seções). `only_open`: só pendentes e em execução."""
        pass

    @abstractmethod
    def apply_template_version(self, form: Form, template_id: str) -> Optional[Form]:
        """Grava as seções, os motivos e a versão de template que `form` já
        recebeu (`Form.apply_template_version`) — só se no banco ele ainda for
        deste template e estiver aberto. `None` quando mudou nesse meio-tempo
        (foi concluído, cancelado ou removido)."""
        pass
