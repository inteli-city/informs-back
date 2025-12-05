from abc import ABC, abstractmethod
from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS


class IFormRepository(ABC):

    @abstractmethod
    def get_form_by_id(self, user_id:str, form_id: str) -> Form:
        pass
    
    @abstractmethod
    def get_form_by_user_id(self, user_id: str) -> List[Form]:
        pass

    @abstractmethod
    def get_all_forms(self, page: int, limit: int, status: Optional[FORM_STATUS] = None, system: Optional[str] = None, user_id: Optional[str] = None, created_at_start: Optional[int] = None, created_at_end: Optional[int] = None, search: Optional[str] = None) -> List[Form]:
        pass

    @abstractmethod
    def create_form(self, form: Form) -> Form:
        pass

    @abstractmethod
    def update_form(
        self,
        user_id: str,
        form_id: str,
        status: Optional[FORM_STATUS] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        sections: Optional[List[Section]] = None,
        justification: Optional[Justification] = None,
        vinculation_form_id: Optional[str] = None,
        extra_fields: Optional[dict] = None,
    ) -> Form:
        pass

    @abstractmethod
    def cancel_form(self, user_id: str, form_id: str, justification: Justification, cancelled_at: int, updated_at: int) -> Form:
        pass

    @abstractmethod
    def complete_form(self, user_id: str, form_id: str, sections: List[Section], completed_at: int, updated_at: int) -> Form:
        pass
