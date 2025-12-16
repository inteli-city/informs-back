from abc import ABC, abstractmethod
from typing import List, Optional

from src.shared.domain.entities.template import Template


class ITemplateRepository(ABC):

    @abstractmethod
    def create_template(self, template: Template) -> Template:
        pass

    @abstractmethod
    def get_template(self, template_id: str) -> Optional[Template]:
        pass

    @abstractmethod
    def get_all_templates(self) -> List[Template]:
        pass

    @abstractmethod
    def update_template(self, template: Template) -> Template:
        pass
