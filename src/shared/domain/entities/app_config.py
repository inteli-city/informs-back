from copy import deepcopy
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, ValidationError

from src.shared.helpers.errors.domain_errors import EntityError


class _ConfigGroup(BaseModel):
    # Chave desconhecida é erro, não silêncio: um typo no admin ("cancel_from")
    # viraria uma feature que nunca liga. Pelo mesmo motivo os tipos são
    # estritos — "no" não vira False.
    model_config = ConfigDict(extra="forbid")


class MenusConfig(_ConfigGroup):
    """Quais menus e botões o app mostra. O papel do usuário continua valendo
    por cima disto — `start_tracking` ligado não mostra o botão a quem não é
    INSPECTOR."""

    create_form: StrictBool = True
    start_tracking: StrictBool = True
    route_plan: StrictBool = True


class MapConfig(_ConfigGroup):
    # Zoom a partir do qual os pins deixam de agrupar (maxZoom do Supercluster).
    cluster_max_zoom: StrictInt = Field(default=16, ge=0, le=22)


class TextsConfig(_ConfigGroup):
    claim_action_label: StrictStr = Field(default="Assumir formulário", min_length=1, max_length=40)


class FlowsConfig(_ConfigGroup):
    open_form_after_claim: StrictBool = False
    return_to_map_after_submit: StrictBool = False
    cancel_form: StrictBool = False


class PreviewConfig(_ConfigGroup):
    # Imagens dos campos informativos (FILE/URL_INFORMATION_FIELD de imagem)
    # na prévia da OS no mapa.
    information_images: StrictBool = False


class CreationConfig(_ConfigGroup):
    # Criar formulário "em aberto" para o sistema (sem dono), além de "para mim".
    # No back-end, um formulário sem `user_id` continua exigindo
    # `SystemConfig.allow_unassigned_forms` — esta chave só oferece a opção no app.
    allow_open: StrictBool = False


class AppConfig(_ConfigGroup):
    """
    Configuração da aplicação vista pelo app de campo.

    Vem em camadas, da mais geral para a mais específica:
        1. os defaults deste esquema — o app como ele é hoje;
        2. o padrão da aplicação, editado pelo admin da plataforma;
        3. as diferenças de um sistema, editadas pelo admin do sistema.

    Cada camada guardada é parcial: só as chaves que ela muda. O que o app
    recebe é a soma das três (`resolve`). Uma chave nova entra aqui com
    default igual ao comportamento atual, e nenhum sistema muda sem pedir.
    """

    menus: MenusConfig = Field(default_factory=MenusConfig)
    map: MapConfig = Field(default_factory=MapConfig)
    texts: TextsConfig = Field(default_factory=TextsConfig)
    flows: FlowsConfig = Field(default_factory=FlowsConfig)
    preview: PreviewConfig = Field(default_factory=PreviewConfig)
    creation: CreationConfig = Field(default_factory=CreationConfig)

    @staticmethod
    def validate_layer(values: Dict[str, Any]) -> Dict[str, Any]:
        """Confere uma camada parcial contra o esquema e a devolve intacta —
        guardamos só o que a camada muda, nunca a configuração expandida."""
        if not isinstance(values, dict):
            raise EntityError("Configuração da aplicação deve ser um objeto")
        AppConfig._parse(values)
        return deepcopy(values)

    @staticmethod
    def resolve(*layers: Optional[Dict[str, Any]]) -> "AppConfig":
        merged: Dict[str, Any] = {}
        for layer in layers:
            if layer:
                merged = _deep_merge(merged, layer)
        return AppConfig._parse(merged)

    @staticmethod
    def effective(
        default_layer: Optional[Dict[str, Any]],
        system_layer: Optional[Dict[str, Any]],
        allows_unassigned_forms: bool,
    ) -> "AppConfig":
        """Configuração que vale para um sistema: as camadas somadas, mais as
        regras que dependem do resto da `SystemConfig`. `creation.allow_open`
        só fica ligada se o sistema aceita formulário sem dono — senão o app
        ofereceria criar em aberto e o `POST /forms` recusaria."""
        config = AppConfig.resolve(default_layer, system_layer)
        if not allows_unassigned_forms:
            config.creation.allow_open = False
        return config

    @staticmethod
    def _parse(values: Dict[str, Any]) -> "AppConfig":
        try:
            return AppConfig.model_validate(values)
        except ValidationError as err:
            first = err.errors()[0]
            path = ".".join(str(part) for part in first["loc"])
            raise EntityError(f"Configuração da aplicação inválida em '{path}': {first['msg']}")


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
