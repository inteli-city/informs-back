# ADR-0010: Sincronização com Sistema de Origem (Oracle Apex)

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: sincronização, apex, oracle, eventbridge, integração, batch

## Contexto

Formulários criados e preenchidos no Informs precisam ser enviados ao sistema de origem (Oracle Apex) para processamento downstream. A sincronização precisa:

- Executar periodicamente sem intervenção manual
- Lidar com falhas parciais (alguns formulários falham, outros succedem)
- Manter checkpoint para não reprocessar formulários já enviados
- Suportar múltiplos sistemas de origem (GAIA, SGC, etc.) com URLs diferentes
- Registrar e permitir retry de formulários com erro

## Decisão

Implementamos um **job de sincronização scheduled via EventBridge** com rastreamento de estado e gestão de erros.

**Arquitetura da sincronização:**

```
EventBridge (cron) → sync_forms_origin (Lambda)
                         ├── Query DynamoDB (forms updated since checkpoint)
                         ├── Batch (100 forms per request)
                         ├── POST → Oracle Apex REST API
                         ├── Update SyncState (checkpoint)
                         └── Upsert SyncErrorForm (falhas)

Oracle Apex → sync_forms_origin_callback (Lambda via API Gateway)
                 └── Registra form_ids com erro no DynamoDB
```

**Módulos envolvidos:**
- `sync_forms_origin` — Job scheduled: busca, agrupa e envia formulários
- `sync_forms_origin_callback` — Webhook: recebe callbacks de erro do Apex

**Entidades de suporte:**
- `SyncState` — Checkpoint por job/sistema (`job_name`, `system`, `checkpoint_synced_at`, `status`)
  - Status: `IDLE`, `RUNNING`, `COMPLETED`, `FAILED`
- `SyncErrorForm` — Formulários com erro de sync (`form_id`, `job_name`, `system`, `last_failed_at`)

**Fluxo detalhado do sync_forms_origin:**
1. Para cada sistema configurado (GAIA, SGC, etc.):
   a. Busca `SyncState` → obtém `checkpoint_synced_at`
   b. Query GSI2 por `system` com `updated_at >= checkpoint`
   c. Também busca `SyncErrorForm` para retry de formulários com erro anterior
   d. Agrupa em batches de 100 formulários
   e. Para cada batch: POST ao endpoint Apex com `{"forms": [...], "execution_id": "..."}`
   f. Se sucesso: atualiza checkpoint, limpa erros
   g. Se falha: registra `SyncErrorForm` para retry futuro

**Configuração via environment:**
- `SYNC_FORMS_PAGE_LIMIT` — Tamanho do batch (default: 100)
- `SYNC_FORMS_WINDOW_MINUTES` — Janela de tempo para busca (default: 10 min)
- `SYNC_FORMS_TIMEOUT` — Timeout da chamada HTTP ao Apex (default: 20s)
- URLs por sistema: `DEFAULT_URL_TEMPLATE`, `GAIA_URL_TEMPLATE`

**Métricas coletadas (logs):**
- Formulários enviados, falhas, páginas carregadas
- Tempo de execução por sistema
- Erros retried com sucesso

## Consequências

### Positivas
- Sincronização automática sem intervenção manual
- Checkpoint evita reprocessamento — apenas formulários novos/alterados são enviados
- Retry automático de formulários com erro em execuções futuras
- Batch processing reduz número de chamadas HTTP ao Apex
- Isolamento por sistema — falha no GAIA não afeta SGC

### Negativas
- Eventual consistency — formulários não são enviados em tempo real
- Timeout de 20s por batch pode não ser suficiente para batches grandes
- Se o Apex estiver fora, erros acumulam até a próxima janela
- Callback depende do Apex implementar a chamada de retorno corretamente
- Sem dead-letter queue — formulários com erro persistente ficam em retry indefinido

## Alternativas Consideradas

### Sync em tempo real (evento por formulário)
- **Descrição**: Enviar cada formulário ao Apex imediatamente após submissão via SQS/SNS
- **Motivo da rejeição**: Maior complexidade; Apex pode não suportar alta taxa de requests individuais; batch é mais eficiente

### Sync via exportação de arquivo (CSV/JSON no S3)
- **Descrição**: Gerar arquivo periódico no S3 para o Apex consumir
- **Motivo da rejeição**: Maior latência; requer implementação de polling no lado do Apex; sem feedback de erros por formulário
