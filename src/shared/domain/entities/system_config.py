import abc
from typing import Any, Dict, List, Optional

from src.shared.domain.entities.app_config import AppConfig
from src.shared.helpers.errors.domain_errors import EntityError


class SystemConfig(abc.ABC):
    """
    Configuração por contrato (`system`), especificação Uberlândia §7.2.

    Ausência de `SystemConfig` para um `system` equivale aos defaults desta
    classe — nenhum sistema existente (Gaia, Geovista, SGC) precisa de um
    item cadastrado para continuar funcionando como hoje.

    `app_config` é a camada do sistema na configuração da aplicação: só as
    chaves que este sistema muda em relação ao padrão (ver `AppConfig`).
    `app_config_version` sobe a cada alteração dessa camada.
    """

    system: str
    scope_keys: List[str]
    scope_partition_key: Optional[str]
    geofence_radius_m: Optional[float]
    allow_unassigned_forms: bool
    app_config: Dict[str, Any]
    app_config_version: int
    created_at: int
    updated_at: int

    def __init__(
        self,
        system: str,
        created_at: int,
        updated_at: int,
        scope_keys: Optional[List[str]] = None,
        scope_partition_key: Optional[str] = None,
        geofence_radius_m: Optional[float] = None,
        allow_unassigned_forms: bool = False,
        app_config: Optional[Dict[str, Any]] = None,
        app_config_version: int = 0,
    ):
        if not isinstance(system, str) or not system.strip():
            raise EntityError("Sistema deve ser uma string não vazia")
        self.system = system

        scope_keys = scope_keys if scope_keys is not None else []
        if not isinstance(scope_keys, list) or not all(isinstance(k, str) for k in scope_keys):
            raise EntityError("scope_keys deve ser uma lista de strings")
        self.scope_keys = scope_keys

        if scope_partition_key is not None and not isinstance(scope_partition_key, str):
            raise EntityError("scope_partition_key deve ser uma string ou null")
        self.scope_partition_key = scope_partition_key

        if geofence_radius_m is not None and not isinstance(geofence_radius_m, (int, float)):
            raise EntityError("geofence_radius_m deve ser um número ou null")
        self.geofence_radius_m = float(geofence_radius_m) if geofence_radius_m is not None else None

        if not isinstance(allow_unassigned_forms, bool):
            raise EntityError("allow_unassigned_forms deve ser verdadeiro ou falso")
        self.allow_unassigned_forms = allow_unassigned_forms

        self.app_config = AppConfig.validate_layer(app_config if app_config is not None else {})

        if not _is_int(app_config_version) or app_config_version < 0:
            raise EntityError("app_config_version deve ser um inteiro não negativo")
        self.app_config_version = app_config_version

        if not _is_int(created_at):
            raise EntityError("Timestamp de criação deve ser um inteiro")
        self.created_at = created_at

        if not _is_int(updated_at):
            raise EntityError("Timestamp de atualização deve ser um inteiro")
        self.updated_at = updated_at


def _is_int(value) -> bool:
    # bool é subclasse de int em Python: True passaria como 1.
    return isinstance(value, int) and not isinstance(value, bool)
