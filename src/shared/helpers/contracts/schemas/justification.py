from pydantic import BaseModel


class JustificationOptionSchema(BaseModel):
    option: str
    required_image: bool = False
    required_text: bool = False


class JustificationSelectedSchema(BaseModel):
    option: str
    text: str | None = None
    image_url: str | None = None


class JustificationSchema(BaseModel):
    options: list[JustificationOptionSchema]
    selected: JustificationSelectedSchema | None = None
