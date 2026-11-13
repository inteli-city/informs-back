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

Cada definição tem uma chave única dentro do template, rótulo, tipo, obrigatoriedade e, apenas para arquivo, `file_type` opcional (`IMAGE` ou `DOCUMENT`). Tipos disponíveis: `TEXT_INFORMATION_FIELD`, `MAP_INFORMATION_FIELD`, `FILE_INFORMATION_FIELD` e `URL_INFORMATION_FIELD`. Para editar, envie a lista completa; `[]` remove as definições. Alterar a lista salva no lugar, sem versão nova, mesmo em template já em uso (ADR-0025). As regras valem para novas criações; propagar seções não modifica os dados informativos de formulários existentes.

Na criação, envie os valores no `POST /forms` com a mesma `key` e o mesmo `information_field_type`. É possível enviar campos informativos adicionais sem chave para manter integrações existentes. Exemplo para arquivo:

```json
"information_fields": [
  {
    "key": "foto_evidencia",
    "information_field_type": "FILE_INFORMATION_FIELD",
    "filename": "evidencia.jpg",
    "mimetype": "image/jpeg",
    "file_type": "IMAGE"
  }
]
```

Sem um campo obrigatório, com chave repetida, tipo divergente ou MIME incompatível com a categoria configurada, a criação retorna erro. A chave é preservada no formulário retornado. A confirmação do arquivo segue o contrato existente: o `POST` retorna uma URL pré-assinada e o cliente deve enviar os bytes por `PUT`. **A validação na criação comprova a declaração do arquivo, não a presença dos bytes no armazenamento.** O cliente deve tratar falhas de upload e não anunciar que o arquivo está disponível antes do PUT bem-sucedido.

Integrações que já hospedam o arquivo (ex.: Apex) podem atender uma definição `FILE_INFORMATION_FIELD` com um link, sem upload ([ADR-0026](adr/0026-campo-de-arquivo-aceita-link-de-integracao.md)). Envie `URL_INFORMATION_FIELD` com a mesma `key`, a `url` e o `mimetype` do arquivo. Se a definição tiver `file_type`, o `mimetype` precisa ser da mesma categoria (`image/*` para `IMAGE`). O valor fica gravado como link; o inverso (arquivo numa definição de link) segue recusado.

```json
"information_fields": [
  {
    "key": "foto_evidencia",
    "information_field_type": "URL_INFORMATION_FIELD",
    "url": "https://apex.exemplo/fotos/123.jpg",
    "mimetype": "image/jpeg"
  }
]
```

A tela web e o app devem implementar a edição das definições e a seleção/envio dos valores para usar este contrato; a API sozinha não adiciona essa interface. Confirme a compatibilidade dos clientes antes de tornar uma definição obrigatória em template utilizado por eles.
