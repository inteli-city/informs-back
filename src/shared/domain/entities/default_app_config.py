import abc
from typing import Any, Dict, Optional

from src.shared.domain.entities.app_config import AppConfig
from src.shared.helpers.errors.domain_errors import EntityError


class DefaultAppConfig(abc.ABC):
    """
    Padrão da aplicação: a camada de `AppConfig` que vale para todo sistema
    que não sobrescreve a chave. Guarda só as chaves que o admin da plataforma
    mudou em relação aos defaults do esquema.

    Ausência do item equivale a `values = {}` — o app como ele é hoje.
    """

    values: Dict[str, Any]
    version: int
    updated_at: int
    updated_by: Optional[str]

    def __init__(
        self,
        values: Dict[str, Any],
        version: int,
        updated_at: int,
        updated_by: Optional[str] = None,
    ):
        self.values = AppConfig.validate_layer(values)

        if not isinstance(version, int) or isinstance(version, bool) or version < 0:
            raise EntityError("Versão do padrão da aplicação deve ser um inteiro não negativo")
        self.version = version

        if not isinstance(updated_at, int) or isinstance(updated_at, bool):
            raise EntityError("Timestamp de atualização deve ser um inteiro")
        self.updated_at = updated_at

        if updated_by is not None and not isinstance(updated_by, str):
            raise EntityError("updated_by deve ser uma string ou null")
        self.updated_by = updated_by
