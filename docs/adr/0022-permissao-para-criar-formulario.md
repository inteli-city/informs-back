# ADR-0022: Permissão `forms.create` para criar formulário pelo app

**Status**: Aceito

**Data**: 2026-11-09

**Decisores**: Equipe Intelicity

**Tags**: rbac, formulários, app-config, autorização

## Contexto

A aba "Criar" do app e o `POST /forms` dependiam só da configuração da aplicação (`menus.create_form`, por sistema). Esse ajuste vale para todos do sistema: não dava para deixar um perfil criar e outro não.

O catálogo de ações da ADR-0020 já tem esse modelo para o percurso: `tracking.start` (a pessoa pode) **e** `menus.start_tracking` (o sistema mostra o botão), no mesmo sistema.

## Decisão

- Nova ação no catálogo: `forms.create` — "Criar formulários pelo app (aba Criar)".
- Criar formulário exige, **no mesmo sistema**, o menu `create_form` ligado **e** `forms.create` no papel da pessoa. Permissão num sistema e menu ligado em outro não somam.
- ADMIN do sistema e super admin continuam passando direto, com ou sem menu (é como as integrações criam as OS do pool).
- A regra vale no app (a aba e o passo "Sistema" do Criar) e no `POST /forms` (`ForbiddenAction`).
- Sem migração automática: quem administra cada sistema marca `forms.create` nos papéis que devem criar, na tela de Papéis — de preferência no papel padrão, que é dado a quem entra no sistema pela primeira vez.

## Consequências

### Positivas
- Cada sistema escolhe, por papel, quem vê a aba Criar, sem deploy.
- Mesmo padrão do percurso: config liga a função no sistema, a ação libera para o perfil.

### Negativas
- No deploy, papéis existentes ficam sem `forms.create`: só ADMIN e super admin criam até alguém marcar a ação nos papéis. Aceito porque hoje só um sistema usa a criação pelo app.
- Pessoa sem vínculo no sistema (sistema sem papel padrão) não cria.
