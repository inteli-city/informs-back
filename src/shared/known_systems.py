"""
Sistemas conhecidos que integram com o Informs.

Fonte única para o mapeamento de origem (sync_forms_origin) e para a
validação de cobertura da reconciliação (reconcile_form_files). Sem isto, os
dois podiam divergir silenciosamente sobre quais sistemas existem — um
sistema novo adicionado aqui para habilitar o sync automaticamente passa a
ser cobrado também pela reconciliação, em vez de depender de alguém lembrar
de atualizar o RECONCILE_SYSTEMS à parte.
"""

SYSTEM_TO_ORIGIN = {
    "GAIA": "gaia",
    "GIPAV": "servicos_poa",
}
KNOWN_SYSTEMS = tuple(SYSTEM_TO_ORIGIN)
