from typing import Any, Optional
from warnings import warn

from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse


class HttpRequest(IRequest):
    body: Any
    headers: dict
    query_params: dict
    path_params: dict
    data: dict

    def __init__(
        self,
        body: Optional[Any] = None,
        headers: Optional[dict] = None,
        query_params: Optional[dict] = None,
        path_params: Optional[dict] = None,
    ):
        self.body = body or {}
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.path_params = path_params or {}
        data_dict = {}

        if isinstance(body, dict):
            overlaps = sorted(set(self.body).intersection(self.query_params))
            if overlaps:
                warn(f"body and query_params have overlapping keys -> {overlaps}")

        if isinstance(body, str):
            data_dict.update({"body": body})

        # Headers HTTP não são parâmetros: ficam só em `self.headers`. Antes eles
        # entravam em `data`, e header que o navegador manda sozinho virava
        # campo de negócio com o mesmo nome — "Priority" (RFC 9218) sobre
        # `priority`, e "Origin" (todo POST do app web) no `origin` opcional do
        # POST /forms, que respondia 400 "Parâmetro inválido: origin".
        # Ordem de precedência: body vence por último. Query string chega
        # sempre como string e não deve sobrescrever um campo do payload JSON.
        data_dict.update(self.query_params)
        data_dict.update(self.path_params)
        if isinstance(body, dict):
            data_dict.update(body)
        self.data = data_dict

    @property
    def data(self) -> dict:
        return self._data

    @data.setter
    def data(self, value: dict):
        self._data = value

    def __repr__(self):
        return (
            f"HttpRequest (body={self.body}, headers={self.headers}, query_params={self.query_params}, data={self.data})"
        )


class HttpResponse(IResponse):
    status_code: int
    body: Any
    headers: dict
    data: dict

    def __init__(
        self,
        status_code: int,
        body: Optional[Any] = None,
        headers: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        resolved_data = data or {}

        self.status_code = status_code
        self.body = body if body is not None else resolved_data
        self.headers = dict(headers or {})

        data_dict = {}
        if isinstance(self.body, dict):
            data_dict.update(self.body)
        elif isinstance(self.body, str):
            data_dict.update({"body": self.body})

        data_dict.update(self.headers)
        self.data = data_dict

    @property
    def data(self) -> dict:
        return self._data

    @data.setter
    def data(self, value: dict):
        self._data = value

    @property
    def status_code(self) -> int:
        return self._status_code

    @status_code.setter
    def status_code(self, value: int):
        self._status_code = value

    def __repr__(self):
        return (
            f"HttpResponse (status_code={self.status_code}, body={self.body}, headers={self.headers})"
        )
