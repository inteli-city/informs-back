from typing import Literal

from src.shared.helpers.contracts.base import ResponseContractModel
from src.shared.helpers.contracts.schemas.form import FormResponseSchema


class RemovedFormMarkerSchema(ResponseContractModel):
    """OS que saiu do pool numa consulta incremental (`updated_after`). Só estes campos: o formulário não é
    mais do pool, então não se expõe o resto dele a quem não o tem mais."""

    id: str
    status: str
    possession: str
    updated_at: int
    removed_from_pool: Literal[True]


class GetAllFormsResponseSchema(ResponseContractModel):
    # Na lista do delta, um item é o formulário completo ou o marcador de saída. Sem o marcador o contrato
    # de hoje rejeitaria a OS que saiu do pool.
    forms: list[FormResponseSchema | RemovedFormMarkerSchema]
    limit: int | None = None
    last_evaluated_key: str | None = None
    # Só vem numa consulta incremental; sem `updated_after` a resposta não tem a chave.
    server_time: int | None = None
