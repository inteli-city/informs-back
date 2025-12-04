from typing import List, Optional

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository


class GetAllFormsUsecase:
    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(
        self,
        requester_user_id: str,
        page: int,
        limit: int,
        status: Optional[FORM_STATUS] = None,
        system: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[Form]:
        return self.form_repo.get_all_forms(
            page=page,
            limit=limit,
            status=status,
            system=system,
            user_id=requester_user_id,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
            search=search,
        )
