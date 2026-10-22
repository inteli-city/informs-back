"""Pasta fixa de saída do e2e local. Sem efeitos colaterais: o teste importa este módulo sem subir o e2e."""

from pathlib import Path

PASTA_SAIDA = Path(__file__).resolve().parent / ".e2e-saida"


def pasta_de_saida(saida: str) -> Path:
    """Resolve o `--saida` dentro de `PASTA_SAIDA` e recusa qualquer caminho que saia dela.

    `..` e caminho absoluto são resolvidos antes da comparação: um caminho que termine fora da
    pasta fixa é recusado, mesmo que pareça relativo na linha de comando.
    """
    base = PASTA_SAIDA.resolve()
    destino = (PASTA_SAIDA / saida).resolve()
    if not destino.is_relative_to(base):
        raise SystemExit(f"--saida recusado: a pasta de saída precisa ficar dentro de {base}")
    return destino
