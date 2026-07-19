from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt

# StrictInt rejeita bool (subclasse de int, que o Pydantic aceitaria como int).
# Contrapartida Pydantic de src/shared/domain/validators.ensure_non_negative_int —
# mantenha os dois em sincronia.
NonNegativeStrictInt = Annotated[StrictInt, Field(ge=0)]


class RequestContractModel(BaseModel):
    # request.data contém headers/query/path além do body;
    # ignoramos extras para validar apenas o contrato do endpoint.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class ResponseContractModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
