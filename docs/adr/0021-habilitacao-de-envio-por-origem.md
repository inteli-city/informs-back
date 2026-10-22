# ADR-0021: Habilitação do envio ao Apex por origem, sem ligar as demais

**Status**: Aceito

**Data**: 2026-10-22

**Decisores**: Equipe Intelicity

**Tags**: sincronização, apex, uberlandia, trava, incidente

## Contexto

A sincronização com o Apex (ADR-0010) envia formulários ao endpoint de produção, e não existe sandbox do Apex por ambiente. Em 08/09/2026, o sync de dev enviou formulários de teste ao Apex de produção. A resposta foi uma trava global: `APEX_SYNC_ENABLED`, com padrão ligado só em PROD. Fora de PROD, o sync avança o checkpoint e não envia.

Uberlândia é um novo sistema de origem (91 formulários em dev), com endpoint próprio no mesmo host do GAIA e alias `supervisao`. Ele precisa ser testado no stage DEV do Informs contra o Apex real. A trava global não permite isso sem ligar também o GAIA e o GIPAV em DEV, o que recria o risco do incidente.

## Decisão

- O envio de cada origem passa a valer se a trava global estiver ligada **ou** se a origem estiver em `APEX_SYNC_ENABLED_ORIGINS` (lista separada por vírgula, vazia por padrão, normalizada em minúsculas). A trava global não muda.
- Origem listada que não existe em `SYSTEM_TO_ORIGIN` é ignorada, com aviso no log. Um nome errado não habilita outra origem.
- A lista chega à Lambda `sync_forms_origin` pelo contexto do CDK (`cdk deploy -c apex_sync_enabled_origins=uberlandia`), e só a ela. O padrão é vazio.
- Cada origem tem o próprio modelo de URL e alias (`ORIGIN_ROUTES` em `OriginRepositoryApex`). Uberlândia usa o host do GAIA com o alias `supervisao`.
- `APEX_URL_<ORIGEM>` troca a URL inteira de uma origem, sem deploy de código.

## Consequências

- Habilitar Uberlândia em DEV é uma decisão de deploy, registrada no comando. Nada é ligado por padrão, e GAIA e GIPAV continuam sem envio fora de PROD.
- A reconciliação (`reconcile_form_files`) passa a cobrar Uberlândia, porque ela está em `SYSTEM_TO_ORIGIN`. Enquanto `RECONCILE_SYSTEMS` não listar `UBERLANDIA`, a reconciliação registra o sistema como sem monitoramento. Ela não deixa de rodar.
- O teste de envio por origem (`tests/shared/infra/repositories/test_origin_repository_apex_uberlandia.py`) prova que listar Uberlândia não liga o GAIA, e que lista vazia mantém o comportamento de antes.
- Não foi feito: envio real ao Apex. A validação de Uberlândia em DEV depende de um Apex de teste ou de uma janela combinada com quem opera o endpoint.

## Alternativas consideradas

- **Trava global por stage com exceção por sistema no código**: descartada. A exceção ficaria no código, e a decisão de ligar um sistema em DEV exigiria deploy de código.
- **Sandbox do Apex por ambiente**: não existe. Pedir ao Apex um sandbox continua pendente, e esta ADR não depende dele.
- **Ligar a trava global em DEV**: descartada. Reabre o risco do incidente de 08/09/2026 para GAIA e GIPAV.
