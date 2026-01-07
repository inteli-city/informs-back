from typing import List, Optional, Tuple

from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import InvalidPaginationToken
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token


class GetAllFormsUsecase:
    def __init__(self, form_repo: IFormRepository):
        self.form_repo = form_repo

    def __call__(
        self,
        requester_user_id: str,
        limit: int,
        exclusive_start_key: Optional[str] = None,
        status: Optional[FORM_STATUS] = None,
        system: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        start_key = None
        if exclusive_start_key is not None:
            start_key = try_decode_pagination_token(exclusive_start_key)
            if start_key is None:
                raise InvalidPaginationToken()

        return self.form_repo.get_all_forms(
            limit=limit,
            exclusive_start_key=start_key,
            status=status,
            system=system,
            user_id=requester_user_id,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
            search=search,
        )
