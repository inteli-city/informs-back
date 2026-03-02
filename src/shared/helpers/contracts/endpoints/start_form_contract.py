from src.shared.helpers.contracts.base import RequestContractModel


class StartFormRequestSchema(RequestContractModel):
    in_progress_at: int
