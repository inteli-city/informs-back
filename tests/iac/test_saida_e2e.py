"""A saída do e2e local fica dentro da pasta fixa; caminho que sai dela é recusado antes de rodar."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "iac" / "local"))

from saida_e2e import PASTA_SAIDA, pasta_de_saida  # noqa: E402


def test_subpasta_dentro_da_pasta_fixa_e_aceita():
    assert pasta_de_saida("rodada-1") == (PASTA_SAIDA / "rodada-1").resolve()


@pytest.mark.parametrize("saida", ["../../../etc", "rodada/../../fora", "/tmp/fora-do-repositorio"])
def test_caminho_que_sai_da_pasta_e_recusado(saida):
    with pytest.raises(SystemExit) as erro:
        pasta_de_saida(saida)
    assert "recusado" in str(erro.value)
