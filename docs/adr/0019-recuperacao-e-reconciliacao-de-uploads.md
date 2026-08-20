# ADR-0019: Recuperação e Reconciliação de Uploads de Arquivos

**Status**: Aceito

**Data**: 2026-08-17

**Decisores**: Equipe Intelicity

**Tags**: s3, upload, presigned-url, observabilidade, confiabilidade, reconciliacao

## Contexto

O [ADR-0005](0005-upload-de-arquivos-via-presigned-urls.md) definiu que o binário nunca passa pelo backend: o cliente recebe presigned URLs e faz `PUT` direto no S3. A consequência não endereçada na época é que **o backend grava a URL final no DynamoDB antes de saber se o upload aconteceu**:

```
App  --POST /submit-->  Lambda  --> gera N presigned URLs
                                --> grava as URLs finais no DynamoDB
                                --> formulário vira COMPLETED
App  --PUT binário-->   S3 direto    (backend não participa, não sabe se deu certo)
```

Isso produziu perda silenciosa e permanente de fotos em produção. Um caso investigado (OS-6179, 12/08/2026) tinha 21 de 38 fotos referenciadas no formulário e ausentes no bucket, com o formulário `COMPLETED` normalmente e nenhum sinal em log ou alarme. O padrão era um prefixo: as 17 primeiras chegaram, o resto não.

Três problemas distintos se somavam:

1. **Cegueira.** Nada no backend compara a URL prometida com o objeto real. O erro do `PUT` morre no app.
2. **Irrecuperabilidade.** Depois do submit o formulário sai de `IN_PROGRESS`, então repetir `/submit` responde 403 (`ForbiddenAction`). Não existia nenhum caminho para obter presigned URL nova, e a URL original expira em 1h. A foto virava perda definitiva.
3. **Propagação.** `sync_forms_origin` envia o formulário `COMPLETED` para o Oracle Apex com as URLs quebradas, sem aviso.

Este ADR trata de (1) e (2). O item (3) segue aberto.

## Decisão

Três medidas independentes, nesta ordem de importância:

### 1. Endpoint de renovação de presigned URL

`POST /forms/{form_id}/files/refresh-presign` re-assina arquivos que o formulário **já referencia**, em qualquer status do formulário.

```
{ "files": [ { "file_url": "...", "mimetype": "image/jpeg" } ] }
  --> { "files": [ { "pre_signed_url": "...", "file_path": "...", "section_id": 1, ... } ] }
```

Regras que definem o desenho:

- **Re-assina a key gravada, nunca gera key nova.** Gerar outra deixaria órfão no bucket e faria a URL do DynamoDB apontar para um objeto que o app não vai enviar. É por isso que não reaproveitamos o `/submit`, que sorteia `uuid4()` por chamada.
- **`Form.stored_files()` é a fronteira de autorização.** Só se re-assina o que já consta no formulário do requester; URL de outro formulário responde 404.
- **`extract_file_path()` recusa URL fora do bucket configurado**, então host arbitrário nunca vira key assinada.
- **O cliente informa o `mimetype`.** A assinatura é específica de `Content-Type`; deduzir da extensão da key devolveria URL que o S3 recusa.

### 2. Job de reconciliação com métrica e alarme

`reconcile_form_files`, agendado de hora em hora, varre formulários `COMPLETED`/`SENT` da janela, compara `Form.stored_files()` com o que existe no bucket e emite as métricas do namespace `Informs`, com alarme em `FormsWithMissingFiles > 0`.

- **Um `list_objects_v2` por raiz de formulário**, não um `HEAD` por arquivo: 38 chamadas viram 1.
- **O prefixo vem do ano gravado na key**, não do `created_at`: formulário criado em dezembro e submetido em janeiro grava no ano do submit.
- **Carência de 30 minutos** (`grace_minutes`): formulário recém-concluído pode ter upload em andamento, e sem isso o job acusaria arquivo que está no meio do caminho.
- **Janela por parâmetro de evento** (`created_at_start`/`created_at_end`), então o backfill histórico é um invoke manual, sem tocar no schedule.
- **O job não escreve nada.** Relatar já resolve a cegueira.

### 3. Validade da presigned URL de 1h para 6h

`DEFAULT_PRESIGN_EXPIRES_IN = 21600`. É folga para a fila de upload, **não** a correção da perda.

Registro explícito da limitação: a URL é assinada com as credenciais temporárias do role da Lambda, e a [documentação da AWS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html#who-presigned-url) diz que *"IAM role credentials – the presigned URL expires when the role session expires, even if you specify a longer expiration time"*. Portanto 6h é teto de melhor esforço, não garantia. Quem torna a falha recuperável é o item 1.

## Consequências

### Positivas

- Falha de upload deixa de ser perda definitiva: o app pede URL nova e retoma.
- A discrepância entre DynamoDB e S3 passa a ser detectada no mesmo dia, com `missing_sample` apontando seção, instância, campo e índice do arquivo ausente.
- O backfill quantifica o estrago histórico, que hoje é desconhecido.
- `Form.stored_files()` centraliza "o que este formulário afirma ter" e serve os dois casos de uso.
- Nenhuma mudança no contrato do `/submit`: o app antigo continua funcionando.

### Negativas

- Mais uma Lambda e mais um schedule para operar.
- O job custa 1 `LIST` por formulário na janela (irrisório, mas não zero) e re-checa o mesmo formulário a cada hora dentro da janela de 24h.
- A reconciliação é posterior ao fato: detecta, não previne.
- Sem estado por arquivo no DynamoDB, o resultado vive só em log/métrica — o front ainda não tem como mostrar "21 fotos não enviadas".
- Superfície de escrita no bucket aumenta: um endpoint autenticado passa a poder emitir URL de `PUT` para key existente, o que permite sobrescrever um arquivo já enviado do próprio formulário.

## Alternativas Consideradas

### S3 Event Notifications (`s3:ObjectCreated:*`) para confirmação em tempo real

- **Descrição**: Lambda disparada pelo bucket confirma cada arquivo que realmente chegou; o path já carrega ano, sistema, form_id, seção e instância.
- **Motivo da rejeição**: é o desenho mais correto a prazo e segue como próximo passo, mas exige estado por arquivo no DynamoDB e configuração de notification no bucket — que **não é gerenciado por este CDK**, só referenciado por nome via `BUCKET_NAME`. Configuração manual em bucket fora do IaC foi exatamente a causa do incidente de CORS em dev/homolog. Importar o bucket para o CDK é pré-requisito.

### Endpoint de confirmação chamado pelo app após cada `PUT`

- **Descrição**: `POST /forms/{id}/files/confirm` a cada upload bem-sucedido.
- **Motivo da rejeição**: falha justamente no cenário que importa. Se o app morre ou perde a rede, ele não confirma nada — e é esse o caso de falha. Além disso não é fonte da verdade: depende do app reportar corretamente. Serve como complemento, nunca sozinho.

### Validar a existência dos arquivos no próprio `/submit`

- **Descrição**: conferir o bucket antes de concluir o formulário.
- **Motivo da rejeição**: inviável por ordem de eventos — no momento do `/submit` o `PUT` ainda não aconteceu.

### Tornar o `/submit` idempotente e devolver as mesmas URLs em nova chamada

- **Descrição**: repetir `/submit` com o formulário já `COMPLETED` responderia 200 com as presigned URLs regeneradas.
- **Motivo da rejeição**: o `/submit` aplica valores de campo e muda o status; reaproveitá-lo como "me dê URLs de novo" mistura duas responsabilidades e deixa o caminho de escrita exposto a um replay de payload divergente. Um endpoint que só re-assina é menor e mais fácil de auditar.

### Apenas aumentar a validade da presigned URL

- **Descrição**: subir `expires_in` e considerar resolvido.
- **Motivo da rejeição**: não cobre o caso real medido. As fotos do incidente somavam ~15 MB depois da compressão do app (1920px, JPEG 75%) — nenhuma rede de campo plausível gasta 1h nisso. Além disso o teto real é a sessão do role da Lambda, não o `ExpiresIn`. Foi adotado como folga, não como solução.

## Pendências

- Importar o bucket S3 para o CDK (pré-requisito para S3 Event Notifications e para não repetir o incidente de CORS).
- Estado por arquivo no DynamoDB e `files_missing_count` no `GET /forms/{id}`, para o front avisar em vez de quebrar a imagem.
- Decidir o comportamento do `sync_forms_origin` diante de formulário incompleto: bloquear, marcar ou seguir enviando.
