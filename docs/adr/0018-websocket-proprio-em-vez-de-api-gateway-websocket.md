# ADR-0018: WebSocket Próprio (FastAPI) em vez de API Gateway WebSocket API

**Status**: Aceito

**Data**: 2026-05-13

**Decisores**: Equipe Intelicity

**Tags**: tracking, websocket, api-gateway, fastapi, arquitetura, aws

## Contexto

A feature de tracking em tempo real de inspectors (ver [ADR-0017](0017-tracking-roles-reuse-profile.md)) precisava de um canal bidirecional: o app do inspector emite localização a cada ~60s e o servidor faz fan-out para os admins conectados assistindo o mapa.

O plano inicial (branch `feat/tracking-and-route-planning`) desenhou essa camada 100% nativa AWS, mantendo a mesma filosofia serverless do resto do Informs:

- **API Gateway WebSocket API** com rotas `$connect` / `$disconnect` / `location` / `ping`
- Uma **tabela `Connection` nova** no DynamoDB (`PK=connection#{connection_id}`), com TTL de 5min para detectar conexões zumbi e 2 GSIs (`ByUser`, `ByRole`) só para viabilizar o fan-out
- Um **Lambda Authorizer** customizado no `$connect` para validar o JWT e cachear role/system/name na Connection
- Fan-out feito chamando `apigatewaymanagementapi.post_to_connection()` para cada `connection_id` de admin, tratando `GoneException` (410) para limpar conexões mortas

Ao detalhar essa implementação, ficou claro que **toda essa tabela `Connection` — e boa parte do desenho — existe apenas porque o API Gateway WebSocket é stateless entre invocações**: cada mensagem chega numa Lambda nova, sem memória do que está conectado. Para saber "quem está online agora" e "para quais `connection_id` fazer fan-out", é obrigatório persistir e manter vivo o `connection_id` de cada socket em algum lugar (daí a tabela + TTL + Authorizer cacheando contexto).

Isso é a complexidade certa para um sistema com muitas instâncias Lambda concorrentes e centenas/milhares de conexões. Não é o nosso caso: o volume estimado era ~15 inspectors emitindo a cada 60s e poucos admins assistindo. Queríamos manter a mesma filosofia de simplicidade do restante do projeto ([ADR-0001](0001-clean-architecture-com-python-e-aws-lambda.md)) — não adicionar uma tabela, um Authorizer e um mecanismo de cleanup só para resolver um problema de escala que não temos.

## Decisão

Rejeitamos o **API Gateway WebSocket API** e implementamos um **serviço WebSocket próprio** (`ws_server/`), em Python com **FastAPI + `websockets`**, rodando como processo único de vida longa (não Lambda).

Isso elimina a necessidade da tabela `Connection` por completo: como o processo é único e mantém o socket aberto na memória durante toda a sessão, o estado de "quem está conectado" vive num `ConnectionRegistry` em memória (`ws_server/presence.py`) — um dict simples, sem TTL, sem persistência, sem `connection_id` para gerenciar. O fan-out é um loop Python direto sobre os sockets abertos, sem chamada a `apigatewaymanagementapi`.

Do desenho original, sobrevive apenas o que resolve um problema real:
- **Tabela `Location`** — sim, precisa persistir histórico de posições (isso é dado de negócio, não estado de conexão)
- **Lookup de role via Profile** — sim, autorização continua sendo necessária, mas acontece no handshake do FastAPI (`ws_server/auth.py`), sem precisar de um Lambda Authorizer dedicado nem cache de contexto numa tabela

**Trade-off assumido conscientemente**: o `ConnectionRegistry` em memória não escala horizontalmente — se um dia precisar de múltiplas instâncias do `ws_server`, precisa migrar para Redis pub/sub (documentado no próprio código, `ws_server/presence.py`). Aceitamos esse limite porque hoje rodamos 1 instância e o volume não justifica o contrário.

**Nota sobre hospedagem**: por não ser Lambda, esse serviço precisa de um host always-on. A primeira tentativa foi AWS Lightsail (Debian + Caddy, provisionado via CDK). Migramos para **Railway** um dia depois por simplicidade operacional (deploy automático via `git push`, sem gerenciar servidor/TLS/systemd manualmente) — decisão de hospedagem, não de arquitetura da aplicação. Ver [ws_server/RAILWAY.md](../../ws_server/RAILWAY.md) para o estado atual do deploy.

## Consequências

### Positivas
- Sem tabela `Connection`, sem TTL de cleanup, sem Lambda Authorizer dedicado — três componentes inteiros que não existem
- Fan-out é código Python direto (`asyncio.gather` sobre sockets abertos), sem chamada de rede extra por destinatário
- Estado de presença (quem está online) é imediato e correto por construção — não depende de um TTL para expirar conexões mortas
- Mais fácil de debugar localmente — é um servidor FastAPI comum, roda com `uvicorn` sem emular API Gateway

### Negativas
- Não é serverless — precisa de um processo sempre rodando (custo fixo, ainda que pequeno) e de deploy/hospedagem separados do resto do Informs
- Não escala horizontalmente sem trabalho adicional (Redis pub/sub) — aceitável no volume atual, mas é uma dívida conhecida
- Introduz uma tecnologia diferente do padrão do resto do repo (FastAPI vs. Lambda handlers Clean Architecture) — únicos módulos do projeto que não seguem presenter/controller/usecase/viewmodel

## Alternativas Consideradas

### API Gateway WebSocket API + tabela Connection + Lambda Authorizer (plano original)
- **Descrição**: Arquitetura 100% serverless nativa AWS — `$connect`/`$disconnect`/rotas customizadas, Connection table com TTL para expirar sockets zumbis, fan-out via `apigatewaymanagementapi.post_to_connection()`
- **Motivo da rejeição**: Toda a complexidade (tabela extra, 2 GSIs, TTL, Lambda Authorizer, tratamento de `GoneException`) existe só para compensar o fato de o API Gateway não manter estado de conexão entre invocações. Para o volume atual (~15 emissores, poucos consumidores), isso é overhead sem benefício — resolve um problema de escala que não temos, ao custo de mais peças para manter.

### AWS AppSync (subscriptions via GraphQL)
- **Descrição**: Usar subscriptions do AppSync como camada realtime gerenciada
- **Motivo da rejeição**: Exigiria modelar o domínio de tracking em GraphQL só para essa feature, sem reuso do padrão REST+Cognito já estabelecido no resto do Informs; não elimina a necessidade de gerenciar estado de assinantes de forma equivalente.
