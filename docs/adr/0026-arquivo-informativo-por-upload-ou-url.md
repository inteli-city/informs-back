# ADR-0026: Campo informativo de arquivo aceita arquivo já hospedado

**Status**: Proposto

**Data**: 2026-11-13

**Decisores**: Equipe Intelicity

**Tags**: templates, campos-informativos, integração, arquivos

## Contexto

O template declara os campos informativos exigidos de quem cria o formulário (ADR-0024), e o valor enviado precisa ter o mesmo `information_field_type` da definição.

Um mesmo template recebe formulários de dois lados:

- quem cria pelo Informs (web/app) tira a foto no aparelho e precisa enviá-la: upload por URL pré-assinada (ADR-0005);
- integrações como o Apex já hospedam a imagem e têm só o endereço dela.

Até aqui o `FILE_INFORMATION_FIELD` só aceitava upload, e a integração mandava a foto como `URL_INFORMATION_FIELD`. Com a regra de tipo idêntico, nenhum tipo de definição servia aos dois lados.

Uma primeira proposta deixava a definição de arquivo aceitar um valor `URL_INFORMATION_FIELD`. Foi descartada: misturava os tipos, e quem monta o template e quem integra precisaria lembrar que "arquivo" às vezes chega e volta como "link".

## Decisão

1. **Cada tipo tem um significado só.**
   - `FILE_INFORMATION_FIELD`: foto ou documento do chamado.
   - `URL_INFORMATION_FIELD`: link externo — site de consulta, portal, página de outro sistema.
2. **O valor de `FILE_INFORMATION_FIELD` é uma união discriminada por `source`:**
   - `"UPLOAD"` (padrão quando `source` não vem): `filename` + `mimetype`. O Informs devolve a URL pré-assinada e o cliente envia os bytes por PUT, como antes.
   - `"URL"`: `url` + `mimetype`. O arquivo já está hospedado por quem cria; o Informs guarda só o endereço, sem upload e sem nada no S3.
3. No `source: "URL"`, a categoria (`file_type`) sai do `mimetype`: `image/*` é `IMAGE`, o resto é `DOCUMENT`. Um `file_type` no corpo que contradiga o `mimetype` é recusado, e a categoria exigida pelo template é conferida como no upload.
4. O formulário guarda e devolve o campo como `FILE_INFORMATION_FIELD`, com `file_path` (a URL do S3 ou o endereço externo) e `source`. Registros sem `source` são upload.
5. Só `source: "UPLOAD"` gera registro de arquivo. Reconciliação de uploads, renovação de URL pré-assinada e limpeza do S3 (ADR-0019) não veem o endereço externo.
6. `URL_INFORMATION_FIELD` não atende definição de arquivo, nem o contrário.

## Consequências

### Positivas
- O mesmo template atende quem cria pelo Informs e quem integra; o tipo da definição diz o que o campo é, e o valor diz como o arquivo chega.
- Arquivo hospedado fora não ocupa armazenamento nem entra nos fluxos de upload.
- Os clientes mostram o campo pelo `file_path` e pelo `file_type`, que já usam; o formato de upload não muda.

### Negativas
- Integrações que mandavam foto como `URL_INFORMATION_FIELD` num campo de arquivo precisam passar a mandar `FILE_INFORMATION_FIELD` com `source: "URL"`.
- O `mimetype` do endereço é declarado por quem integra e não é conferido contra o conteúdo.
- O arquivo depende de quem o hospeda: se o endereço sair do ar, o formulário perde a imagem.
- Formulários antigos podem ter foto em `URL_INFORMATION_FIELD`; os clientes continuam mostrando esse tipo pelo `mimetype` (imagem ou link).

## Alternativas consideradas

### Definição de arquivo aceitar valor `URL_INFORMATION_FIELD`
- **Descrição**: manter os dois tipos de valor e afrouxar a conferência de tipo.
- **Motivo da rejeição**: o tipo deixa de dizer o que o campo é; o formulário guarda "link" para algo que o template chama de "arquivo".

### Tipo de exibição dentro do campo de link
- **Descrição**: definir o campo como link e o app subir o arquivo e preencher o link com o endereço.
- **Motivo da rejeição**: refaz o fluxo de arquivo com outro nome.

### Integração publica o arquivo pelo upload do Informs
- **Descrição**: exigir que o Apex envie os bytes em vez do endereço.
- **Motivo da rejeição**: custo para a integração, que já hospeda a imagem; duplica armazenamento.
