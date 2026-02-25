from pydantic import BaseModel


class StartFormRequestSchema(BaseModel):
    in_progress_at: int
