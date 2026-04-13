# ADR-0005: Upload de Arquivos via Presigned URLs (S3)

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: s3, upload, presigned-url, arquivos, aws

## Contexto

Formulários suportam campos do tipo `FILE_FIELD` e `FILE_INFORMATION_FIELD`, permitindo que usuários anexem imagens e documentos. O sistema precisa:

- Permitir upload de arquivos sem trafegar binários pelo API Gateway/Lambda (limite de 6MB)
- Gerar URLs temporárias e seguras para upload direto ao S3
- Organizar arquivos no S3 de forma que seja possível identificar o contexto (sistema, formulário, seção)
- Suportar múltiplos arquivos por campo (min/max quantity)

## Decisão

Adotamos **Presigned URLs com método PUT** geradas pelo backend. O cliente recebe a URL e faz upload direto ao S3.

**Fluxo:**
1. Cliente envia request de criação/submissão/cancelamento com metadados do arquivo (`filename`, `mimetype`)
2. Backend gera `file_path` (chave S3) e solicita presigned URL ao boto3
3. Backend retorna ao cliente: `pre_signed_url`, `file_path`, `file_url`
4. Cliente faz `PUT` direto na `pre_signed_url` com o conteúdo do arquivo
5. Arquivo fica acessível publicamente via `file_url`

**Estrutura do path S3:**
```
{ano}/{sistema}/{form_id}/{contexto}/{uuid}.{extensão}

Exemplos:
  2025/GAIA/abc-123/sections/1/550e8400-e29b.jpeg        (submit_form)
  2025/GAIA/abc-123/information_field/550e8400-e29b.pdf   (create_form)
  2025/GAIA/abc-123/justification/550e8400-e29b.png       (cancel_form)
```

**Segmentos do path:**
- `ano` — particionamento temporal
- `sistema` — GAIA, SGC, GEOVISTA, INTELIFLEETS (isolamento por sistema)
- `form_id` — vinculação ao formulário
- `contexto` — `sections/{section_id}`, `information_field`, ou `justification`
- `uuid.ext` — nome único gerado + extensão extraída do mimetype

**Módulos que geram presigned URLs:**
- `create_form` — para `information_fields` do tipo `FILE_INFORMATION_FIELD`
- `submit_form` — para campos `FILE_FIELD` nas seções
- `cancel_form` — para `justification_image`

**Configuração:**
- Expiração padrão: 3600 segundos (1 hora)
- Método HTTP: PUT (upload)
- ContentType setado no presigned para validar mimetype

**Entidades envolvidas:**
- `FileUploadRequest` — input mínimo (`filename`, `mimetype`)
- `FileUpload` — output completo (`pre_signed_url`, `file_path`, `file_url`, `section_id`, `field_key`, `file_index`)

## Consequências

### Positivas
- Upload direto ao S3 sem limite de tamanho do API Gateway (6MB)
- Presigned URLs expiram automaticamente — segurança por design
- Path S3 organizado por ano/sistema/formulário facilita auditoria e lifecycle policies
- Backend nunca manipula o binário — menor uso de memória no Lambda
- Suporte a múltiplos arquivos por campo com controle de min/max quantity

### Negativas
- Cliente precisa fazer duas chamadas (API para URL + PUT no S3)
- Se o cliente não fizer o PUT, o campo fica com URL vazia no formulário
- Presigned URLs são temporárias — se expirar antes do upload, precisa gerar novamente
- Sem validação server-side do conteúdo real do arquivo (apenas mimetype declarado)

## Alternativas Consideradas

### Upload via API Gateway (multipart)
- **Descrição**: Enviar arquivo como multipart/form-data pelo API Gateway
- **Motivo da rejeição**: Limite de 10MB no API Gateway; Lambda precisa processar o binário; maior custo de memória e tempo de execução

### Upload via URL assinada POST (S3 POST Policy)
- **Descrição**: Usar POST policies do S3 com formulários HTML
- **Motivo da rejeição**: PUT presigned é mais simples para clientes móveis/SPA; POST policies requerem construção de form fields adicionais
