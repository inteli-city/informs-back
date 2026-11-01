# ADR-0022: Grupos do sistema para direcionar formulários abertos

**Status**: Aceito

**Data**: 2026-11-01

**Decisores**: Tiago Bega

**Tags**: pool, rbac, uberlandia, grupos

## Contexto

O formulário aberto (especificação Uberlândia §6) ficou visível a qualquer pessoa do sistema: o filtro
"fino" foi adiado para uma Fase 2, desenhada como interseção de atributos genéricos (`Form.attributes` x
`Profile.scope`). O planejamento 2027 (IN-1.1) fechou a necessidade de Uberlândia de outro jeito: o
sistema de origem diz **para quais grupos** a OS vai, e só quem está num deles a vê e pega. É a única
funcionalidade bloqueante para Uberlândia entrar em produção.

## Decisão

- Grupo é uma entidade do sistema (`SystemGroup`: `group_id` curto e imutável, `name` editável), gravada na
  tabela de Profiles ao lado dos roles (`system#{system}` / `group#{group_id}`).
- A pessoa recebe grupos no vínculo com o sistema (`SystemMembership.groups`).
- O formulário recebe `groups` na criação; um grupo desconhecido no sistema é recusado (400).
- Uma OS aberta com `groups` só aparece no pool, só abre e só é reivindicada por quem tem ao menos um
  desses grupos. Quem tem `forms.view_all` ainda abre a ficha. Sem `groups`, nada muda.
- O filtro do pool é um `FilterExpression` sobre o GSI3 que já existe; o índice não muda.
- Ação nova `groups.manage` para o catálogo; colocar pessoas em grupos é `users.manage`.
- Apagar grupo em uso (pessoa ou OS aberta) é bloqueado.

Detalhes e o plano de execução: [plano-grupos-do-sistema.md](../plano-grupos-do-sistema.md).

## Consequências

### Positivas
- GAIA e GIPAV não mudam: OS sem `groups` e pessoas sem grupo se comportam como antes.
- O Apex manda uma lista de identificadores legíveis, sem conhecer o modelo de posse.
- Sem índice novo nem migração: os campos são opcionais e ausentes por padrão.

### Negativas
- O `Limit` do pool passa a contar itens antes do filtro: páginas podem vir menores que o limite.
- Uma leitura a mais (o vínculo) em `get_form`, `claim_form` e `GET /forms?scope=pool`.
- `Form.attributes`/`Profile.scope` continuam no modelo, sem uso, até alguém precisar deles.

## Alternativas Consideradas

### Atributos genéricos (`Form.attributes` x `Profile.scope`)
- **Descrição**: o desenho original da especificação, §7.
- **Motivo da rejeição**: o planejamento pediu grupos nomeados e geridos no Informs; atributos livres não
  têm catálogo, então um valor errado não seria detectado.

### Um GSI por grupo (`pool#{system}#{group}`)
- **Descrição**: particionar o pool pelo grupo, como o §14.1 previa para o bairro.
- **Motivo da rejeição**: um formulário pode ir para vários grupos e o atributo do índice tem um valor só.
  O filtro sobre o pool do sistema basta para o volume atual.

### Grupos do Cognito
- **Descrição**: usar grupos do User Pool.
- **Motivo da rejeição**: os grupos do Cognito já significam "sistemas" no token; misturar os dois exigiria
  convenção de nomes e acesso de administração ao Cognito para cada mudança de equipe.
