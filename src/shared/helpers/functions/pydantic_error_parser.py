from pydantic import ValidationError


def _format_loc(loc: tuple) -> str:
    parts = []
    for item in loc:
        if isinstance(item, int):
            if parts:
                parts[-1] = f"{parts[-1]}[{item}]"
            else:
                parts.append(f"[{item}]")
            continue
        if item == "__root__":
            continue
        parts.append(str(item))
    return ".".join(parts) if parts else "payload"


def get_validation_error_message(err: ValidationError) -> str:
    errors = err.errors()
    if not errors:
        return "Parâmetro inválido: payload"

    first_error = errors[0]
    loc = tuple(first_error.get("loc", ()))
    field = _format_loc(loc)
    error_type = first_error.get("type", "")

    if error_type == "missing":
        return f"Parâmetro ausente: {field}"

    return f"Parâmetro inválido: {field}"
