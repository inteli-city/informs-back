from abc import ABC, abstractmethod


class IRequest(ABC):

    @property
    @abstractmethod
    def data(self) -> dict:
        raise NotImplementedError


class IResponse(ABC):

    @property
    @abstractmethod
    def status_code(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def data(self) -> dict:
        raise NotImplementedError
