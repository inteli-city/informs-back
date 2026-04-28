def get_exception_message(error: BaseException) -> str:
    message = str(error)
    return message if message else error.__class__.__name__
