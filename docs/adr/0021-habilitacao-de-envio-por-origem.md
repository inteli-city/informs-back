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
- **Estado em 22/10/2026:** `uberlandia` está ligada em DEV (`cdk deploy -c apex_sync_enabled_origins=uberlandia`). O endpoint foi validado com o responsável do Apex (Henrique Curci) com envios de teste: HTTP 200, `gravados` igual ao enviado. GAIA e GIPAV seguem sem envio fora de PROD.
- **Deploy de DEV:** o workflow `CD.yml` não roda (Actions desligadas). O deploy é local, com `cdk deploy` a partir da máquina de quem tem acesso à conta de DEV, lendo da Lambda implantada os valores que o CD tirava dos secrets e exportando-os sem imprimir. Se o CD voltar, ele precisa de um secret ou variável para passar o contexto `apex_sync_enabled_origins`.
- **Pendência:** `RECONCILE_SYSTEMS` do deploy ainda não lista `UBERLANDIA`; a reconciliação registra um aviso.
- **Deploy local em máquina não-Linux** pode montar a layer com binários da máquina que roda o CDK e derrubar as
  Lambdas na primeira invocação, sem o deploy acusar (o `UPDATE_COMPLETE` não basta): ver o parágrafo
  "Armadilha do deploy local no Mac" do README, com as variáveis `PIP_*` e como conferir depois do deploy.
- O checkpoint avança mesmo quando o Apex falha (a recuperação é pela fila `SyncErrorForm`), e não foi alterado.
- O envio real ao Apex de **produção** não foi feito.

## Alternativas consideradas

- **Trava global por stage com exceção por sistema no código**: descartada. A exceção ficaria no código, e a decisão de ligar um sistema em DEV exigiria deploy de código.
- **Sandbox do Apex por ambiente**: não existe. Pedir ao Apex um sandbox continua pendente, e esta ADR não depende dele.
- **Ligar a trava global em DEV**: descartada. Reabre o risco do incidente de 08/09/2026 para GAIA e GIPAV.
