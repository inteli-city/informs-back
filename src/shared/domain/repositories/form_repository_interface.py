from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

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
    def get_all_forms(
        self,
        limit: int,
        exclusive_start_key: Optional[dict] = None,
        status: Optional[FORM_STATUS] = None,
        system: Optional[str] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
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
    ) -> Form:
        pass
