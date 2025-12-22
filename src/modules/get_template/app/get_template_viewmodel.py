from src.modules.create_template.app.create_template_viewmodel import TemplateViewmodel as BaseTemplateViewmodel
from src.shared.domain.entities.template import Template


class GetTemplateViewmodel(BaseTemplateViewmodel):
    def __init__(self, template: Template):
        super().__init__(template)
