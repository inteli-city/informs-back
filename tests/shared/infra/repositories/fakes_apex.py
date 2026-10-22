"""Dublês do logger e da resposta HTTP dos testes do repositório Apex.

Ficam aqui para que os dois arquivos de teste não repitam as mesmas classes.
"""

class FakeLogger:
    def __init__(self):
        self.events = []

    def info(self, message, extra=None):
        self.events.append(("info", message, extra or {}))

    def warning(self, message, extra=None):
        self.events.append(("warning", message, extra or {}))

    def error(self, message, extra=None):
        self.events.append(("error", message, extra or {}))


class FakeResponse:
    def __init__(self, status: int, body: str):
        self._status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self._status

    def read(self):
        return self._body.encode("utf-8")
