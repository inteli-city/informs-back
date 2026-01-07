from abc import ABC, abstractmethod

from src.shared.domain.entities.form import Form


class IQueueRepository(ABC):

    @abstractmethod
    def send_form(self, form: Form) -> None:
        pass
