# Campos informativos exigidos por template

Decisão e consequências: [ADR-0024](adr/0024-campos-informativos-exigidos-por-template.md).

O template pode declarar `information_fields` para orientar e validar as informações entregues por quem cria o formulário. Esses campos são distintos das seções preenchidas pelo executor. Templates anteriores não possuem exigências e continuam funcionando.

Exemplo no corpo de `POST /templates` ou `PUT /templates/{id}`, junto aos demais campos do template:

```json
"information_fields": [
  {
    "key": "foto_evidencia",
    "label": "Foto de evidência",
    "information_field_type": "FILE_INFORMATION_FIELD",
    "required": true,
    "file_type": "IMAGE"
  }
]
```

Cada definição tem uma chave única dentro do template, rótulo, tipo, obrigatoriedade e, apenas para arquivo, `file_type` opcional (`IMAGE` ou `DOCUMENT`). Para editar, envie a lista completa; `[]` remove as definições. Alterar a lista salva no lugar, sem versão nova, mesmo em template já em uso (ADR-0025). As regras valem para novas criações; propagar seções não modifica os dados informativos de formulários existentes.

Tipos disponíveis e o que cada um significa:

| Tipo | Para quê |
|---|---|
| `TEXT_INFORMATION_FIELD` | texto livre |
| `MAP_INFORMATION_FIELD` | ponto no mapa |
| `FILE_INFORMATION_FIELD` | foto ou documento do chamado, enviado ao Informs ou já hospedado por quem cria |
| `URL_INFORMATION_FIELD` | link externo: site de consulta, portal, página de outro sistema |

Na criação, envie os valores no `POST /forms` com a mesma `key` e o mesmo `information_field_type`. **Sem a `key`, o valor não atende exigência alguma** (é o formato anterior, aceito para manter integrações existentes), e um campo obrigatório falta.

### Arquivo: upload ou endereço ([ADR-0026](adr/0026-arquivo-informativo-por-upload-ou-url.md))

O valor de `FILE_INFORMATION_FIELD` é uma união discriminada por `source`.

**`source: "UPLOAD"`** (padrão quando `source` não vem): o arquivo é enviado ao Informs.

```json
{
  "key": "foto_evidencia",
  "information_field_type": "FILE_INFORMATION_FIELD",
  "filename": "evidencia.jpg",
  "mimetype": "image/jpeg"
}
```

O `POST` retorna uma URL pré-assinada e o cliente deve enviar os bytes por `PUT`. **A validação na criação comprova a declaração do arquivo, não a presença dos bytes no armazenamento.** O cliente deve tratar falhas de upload e não anunciar que o arquivo está disponível antes do PUT bem-sucedido.

**`source: "URL"`**: o arquivo já está hospedado por quem cria (ex.: integração com o Apex). O Informs guarda só o endereço, sem upload e sem ocupar armazenamento.

```json
{
  "key": "foto_evidencia",
  "information_field_type": "FILE_INFORMATION_FIELD",
  "source": "URL",
  "url": "https://apex.exemplo/fotos/123.jpg",
  "mimetype": "image/jpeg"
}
```

A categoria sai do `mimetype`: `image/*` é `IMAGE`, o resto é `DOCUMENT`. Use o tipo real do arquivo (`image/jpeg`, `image/png`, `application/pdf`); um `file_type` no corpo que contradiga o `mimetype` é recusado.

Nos dois casos o formulário devolve `FILE_INFORMATION_FIELD` com `file_path` (URL do armazenamento ou o endereço enviado), `file_type` e `source`.

### Link externo

```json
{
  "key": "consulta_imovel",
  "information_field_type": "URL_INFORMATION_FIELD",
  "url": "https://portal.exemplo/imovel/123",
  "mimetype": "text/html"
}
```

Para site, envie `mimetype: "text/html"`. Foto ou documento vai em `FILE_INFORMATION_FIELD` com `source: "URL"`, não aqui: link não atende definição de arquivo, nem o contrário. Os clientes mostram `URL_INFORMATION_FIELD` pelo `mimetype` (imagem para `image/*`, link para o resto), o que mantém legíveis formulários antigos que guardaram foto como link.

### Erros

Sem um campo obrigatório, com chave repetida, tipo divergente ou categoria de arquivo incompatível com a configurada, a criação retorna erro. A chave é preservada no formulário retornado.

A tela web e o app devem implementar a edição das definições e a seleção/envio dos valores para usar este contrato; a API sozinha não adiciona essa interface. Confirme a compatibilidade dos clientes antes de tornar uma definição obrigatória em template utilizado por eles.
