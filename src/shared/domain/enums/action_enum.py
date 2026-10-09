from enum import Enum


class Action(Enum):
    """
    Catálogo fixo de ações. Cada sistema monta os próprios roles combinando
    estas ações; ação nova só nasce aqui, no código.

    O role ADMIN de um sistema tem todas elas; o super admin tem todas em
    todo sistema.
    """

    FORMS_VIEW_ALL = "forms.view_all"
    FORMS_ASSIGN = "forms.assign"
    FORMS_RELEASE = "forms.release"
    TRACKING_START = "tracking.start"
    TRACKING_VIEW = "tracking.view"
    USERS_MANAGE = "users.manage"
    ROLES_MANAGE = "roles.manage"
    TEMPLATES_MANAGE = "templates.manage"
    APP_CONFIG_EDIT = "app_config.edit"


ACTION_DESCRIPTIONS = {
    Action.FORMS_VIEW_ALL: "Ver os formulários de todos no sistema",
    Action.FORMS_ASSIGN: "Atribuir formulário do pool a uma pessoa",
    Action.FORMS_RELEASE: "Devolver ao pool formulário de outra pessoa",
    Action.TRACKING_START: "Enviar a própria localização (iniciar percurso)",
    Action.TRACKING_VIEW: "Acompanhar a localização e o histórico de percurso das pessoas",
    Action.USERS_MANAGE: "Dar e tirar roles das pessoas do sistema (exceto ADMIN)",
    Action.ROLES_MANAGE: "Criar, editar e apagar os roles do sistema",
    Action.TEMPLATES_MANAGE: "Criar e editar os templates do sistema",
    Action.APP_CONFIG_EDIT: "Editar a configuração da aplicação do sistema",
}
