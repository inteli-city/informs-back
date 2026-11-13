# ADR-0026: Campo informativo de arquivo aceita link de integração

**Status**: Proposto

**Data**: 2026-11-12

**Decisores**: Equipe Intelicity

**Tags**: templates, campos-informativos, integração, arquivos

## Contexto

O template declara os campos informativos exigidos de quem cria o formulário (ADR-0024). Na criação, o valor precisava ter o mesmo `information_field_type` da definição.

Um mesmo template recebe formulários de dois lados:

- quem cria pelo Informs (web/app) envia a foto do aparelho: precisa de `FILE_INFORMATION_FIELD`, com upload por URL pré-assinada (ADR-0005);
- integrações como o Apex já hospedam a imagem e mandam o link: `URL_INFORMATION_FIELD`, com `url` e `mimetype`, sem upload.

Com a regra de tipo idêntico, nenhum tipo servia aos dois: definir como arquivo barrava a integração, e definir como link deixava quem cria pelo Informs sem como enviar a foto.

## Decisão

1. **Uma definição `FILE_INFORMATION_FIELD` também aceita um valor `URL_INFORMATION_FIELD`.** O tipo da definição diz o que o campo é (um arquivo); o valor diz onde ele está.
2. Com `file_type` na definição, a categoria do link sai do `mimetype`: `image/*` é `IMAGE`, o resto é `DOCUMENT`. Categoria divergente é recusada como arquivo divergente.
3. O link é gravado como `URL_INFORMATION_FIELD`, sem upload. Nada passa a supor que ele está no nosso bucket (link pré-assinado, limpeza, reconciliação de uploads).
4. O inverso não vale: definição `URL_INFORMATION_FIELD` continua exigindo link. As demais combinações seguem barradas.

## Consequências

### Positivas
- O mesmo template atende quem cria pelo Informs e quem integra, sem a integração mudar o que envia.
- Os clientes já mostram link com `mimetype` de imagem como imagem; não precisam mudar.
- Arquivo de fora não entra nos fluxos de upload e de armazenamento.

### Negativas
- O formulário pode ter, para a mesma chave, um arquivo ou um link. Quem lê precisa tratar os dois tipos (os clientes atuais já tratam).
- O `mimetype` do link é declarado por quem integra e não é conferido contra o conteúdo; um link errado vale até alguém abrir.
- O link depende de quem o hospeda: se sair do ar, o formulário perde a imagem.

## Alternativas consideradas

### Tipo de exibição dentro do campo de link
- **Descrição**: definir o campo como link e o app subir o arquivo e preencher o link com o endereço.
- **Motivo da rejeição**: refaz o fluxo de arquivo com outro nome, e o tipo da definição deixa de dizer o que o campo exige.

### Integração publica o arquivo pelo upload do Informs
- **Descrição**: exigir que o Apex envie os bytes em vez do link.
- **Motivo da rejeição**: custo para a integração, que já hospeda a imagem; duplica armazenamento.

### Definição com lista de tipos aceitos
- **Descrição**: `accepted_types` na definição, escolhido pelo admin.
- **Motivo da rejeição**: muda o modelo do template, o construtor e a validação para resolver um caso que a regra acima já cobre.
