from enum import Enum


class FileSource(Enum):
    """De onde vem o arquivo de um campo informativo (ADR-0026).

    UPLOAD: enviado ao nosso armazenamento por URL pré-assinada.
    URL: já hospedado por quem criou o formulário; guardamos só o endereço.
    """
    UPLOAD = 'UPLOAD'
    URL = 'URL'
