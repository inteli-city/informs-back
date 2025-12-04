from src.shared.domain.entities.form import Form
from src.shared.domain.enums.form_status_enum import FORM_STATUS


class StartFormViewmodel:
    """
    Minimal viewmodel to expose the updated form status/timestamps after a start.
    The endpoint returns 204 (no body), but keeping the viewmodel aligns the module
    structure with the other handlers and eases future changes.
    """

    def __init__(self, form: Form):
        self.id = form.id
        self.status = form.status
        self.in_progress_at = form.in_progress_at
        self.updated_at = form.updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value if isinstance(self.status, FORM_STATUS) else self.status,
            "in_progress_at": self.in_progress_at,
            "updated_at": self.updated_at,
        }
