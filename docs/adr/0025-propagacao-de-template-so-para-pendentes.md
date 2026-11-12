# ADR-0025: Propagação de template só para formulários pendentes

**Status**: Proposto

**Data**: 2026-11-12

**Decisores**: Equipe Intelicity

**Tags**: templates, versionamento, propagação, offline

## Contexto

Um template em uso muda como nova versão, e o admin escolhe quais formulários abertos passam para ela (propagação). Até aqui, "aberto" era pendente **ou em execução**.

Formulário em execução tem as respostas no aparelho, muitas vezes offline, até o envio. Propagar troca os campos no servidor por baixo do técnico, e o envio chega com respostas da versão anterior. O back aceitava isso no "modo tolerante", mas, como só guarda a versão atual do template, não tem a anterior para conferir. O resultado era:

- resposta de campo removido ou com chave trocada descartada em silêncio;
- envio recusado (o técnico fica travado) quando o campo mudou de tipo ou a opção de lista marcada foi removida;
- cancelamento recusado quando o motivo escolhido saiu da versão nova;
- nenhum campo obrigatório conferido no envio.

Os campos informativos entravam no mesmo versionamento, embora nenhum formulário existente os copie: mudar só eles criava versão nova e oferecia uma propagação sem efeito.

## Decisão

1. **A propagação muda só formulário pendente.** Em execução fica na versão em que o técnico começou e volta como `in_progress` na lista de pulados. Concluído e cancelado seguem como `closed`.
2. A escrita da propagação é condicional a `status = PENDING`: se o técnico iniciar entre a leitura e a escrita, o formulário não muda (`changed`).
3. **Campos informativos mudam sempre no lugar, sem versão nova.** Valem para os formulários criados depois, pelo app ou pela API. Formulários existentes mostram só os campos que eles mesmos guardaram na criação.
4. O modo tolerante do envio continua, só para o caso que sobra: pendente iniciado offline antes de a propagação chegar ao aparelho.

## Consequências

### Positivas
- Quem já começou a preencher nunca perde resposta nem fica travado por causa de uma versão nova.
- Mudar campos informativos não gera versão nem etapa de propagação inútil.
- Nada muda para quem cria formulários: o id do template continua fixo.

### Negativas
- Uma correção no template não chega a formulário em execução; ele termina na versão antiga.
- O caso de pendente iniciado offline continua dependendo do modo tolerante, que não confere obrigatórios. Guardar o histórico de versões resolveria isso (envio validado pela versão em que foi preenchido).

## Alternativas consideradas

### Compatibilizar as respostas na propagação
- **Descrição**: migrar as respostas da versão antiga para a nova (por chave e tipo).
- **Motivo da rejeição**: as respostas de um formulário em execução estão no aparelho, não no servidor; não há o que migrar no momento da propagação.

### Apagar ou reiniciar o formulário em execução
- **Descrição**: invalidar o preenchimento ao propagar.
- **Motivo da rejeição**: perde o trabalho do técnico, inclusive o feito offline.
