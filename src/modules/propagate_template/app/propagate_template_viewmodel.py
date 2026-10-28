from .propagate_template_usecase import PropagationResult
from src.shared.helpers.contracts.endpoints.template_versioning_contract import PropagateTemplateResponseSchema


class PropagateTemplateViewmodel:
    def __init__(self, result: PropagationResult):
        self.result = result

    def to_dict(self):
        payload = {
            "template_version": self.result.template_version,
            "updated": self.result.updated,
            "skipped": [{"form_id": form_id, "reason": reason} for form_id, reason in self.result.skipped],
        }
        return PropagateTemplateResponseSchema.model_validate(payload).model_dump()
