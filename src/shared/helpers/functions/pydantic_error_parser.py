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


_TYPE_LABEL_BY_ERROR = {
    "bool_parsing": "bool",
    "bool_type": "bool",
    "dict_type": "dict",
    "float_type": "float",
    "float_parsing": "float",
    "int_type": "int",
    "int_parsing": "int",
    "list_type": "list",
    "model_type": "dict",
    "string_type": "str",
}


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

    expected_type = _TYPE_LABEL_BY_ERROR.get(error_type)
    if expected_type is not None:
        input_value = first_error.get("input")
        return (
            f"Campo {field} deveria ser do tipo {expected_type}, "
            f"mas foi recebido um campo do tipo {type(input_value)}"
        )

    return f"Parâmetro inválido: {field}"
