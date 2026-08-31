import base64

from src.shared.helpers.errors.domain_errors import EntityError


def ensure_non_negative_int(value, label: str, *, allow_none: bool = False) -> None:
    """Valida "inteiro não negativo" rejeitando bool (subclasse de int em Python).

    Contrapartida de domínio do type alias `NonNegativeStrictInt`
    (src/shared/helpers/contracts/base.py) — mantenha os dois em sincronia.
    """
    if value is None and allow_none:
        return
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EntityError(f"{label} deve ser um inteiro não negativo")


def ensure_valid_sha256_checksum(value, label: str, *, allow_none: bool = False) -> None:
    """Valida Base64 que decodifica para exatamente 32 bytes (digest SHA-256)."""
    if value is None and allow_none:
        return
    if not isinstance(value, str):
        raise EntityError(f"{label} deve ser uma string")
    try:
        if len(base64.b64decode(value, validate=True)) != 32:
            raise ValueError
    except ValueError:
        # binascii.Error é subclasse de ValueError — capturar os dois é redundante.
        raise EntityError(f"{label} deve ser Base64 válido de 32 bytes")
