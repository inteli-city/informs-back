from pydantic import BaseModel, ConfigDict


class RequestContractModel(BaseModel):
    # request.data contém headers/query/path além do body;
    # ignoramos extras para validar apenas o contrato do endpoint.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ResponseContractModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
