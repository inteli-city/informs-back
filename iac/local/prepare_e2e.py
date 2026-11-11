#!/usr/bin/env python3
"""Prepara o banco local para os specs E2E do front (`clients/web/e2e/`).

Liga `allow_unassigned_forms` no GAIA. O seed só faz isso no UBERLANDIA, e
nenhuma rota HTTP expõe essa configuração: sem ela, o cenário de OS de pool
(E-08) não tem como existir. Por isso o ajuste é gravado direto no banco local.

Idempotente: rodar de novo só regrava o mesmo valor. Preserva
`app_config` e `app_config_version`, pelo mesmo motivo de `seed_system_config()`
em `seed_local.py`: o `put` grava o item inteiro.

Uso (com o banco local já de pé, ver `bootstrap_local.py`):
    python iac/local/prepare_e2e.py
"""
import inspect
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_env  # noqa: E402,F401  (precisa vir antes de qualquer src.*)

from src.shared.domain.entities.system_config import SystemConfig  # noqa: E402
from src.shared.environments import Environments  # noqa: E402

E2E_SYSTEM = "GAIA"


def _supports(fn, name: str) -> bool:
    return name in inspect.signature(fn).parameters


def main() -> int:
    repo = Environments.get_system_config_repo()
    current = repo.get_by_system(E2E_SYSTEM)
    now = int(time.time() * 1000)
    kwargs = dict(
        system=E2E_SYSTEM,
        created_at=current.created_at if current else now,
        updated_at=now,
        scope_keys=current.scope_keys if current else None,
        scope_partition_key=current.scope_partition_key if current else None,
        geofence_radius_m=current.geofence_radius_m if current else None,
        allow_unassigned_forms=True,
    )
    for field in ("app_config", "app_config_version"):
        if current is not None and _supports(SystemConfig.__init__, field):
            kwargs[field] = getattr(current, field)
    repo.put(SystemConfig(**kwargs))

    # Relê do repositório: o que vale é o que ficou gravado, não o que foi enviado.
    saved = repo.get_by_system(E2E_SYSTEM)
    if saved is None or saved.allow_unassigned_forms is not True:
        print(f"[erro] {E2E_SYSTEM}: allow_unassigned_forms não ficou True ao reler")
        return 1
    print(f"[ok]   SystemConfig {E2E_SYSTEM}: allow_unassigned_forms=True (relido)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
