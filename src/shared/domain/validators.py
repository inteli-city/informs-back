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
