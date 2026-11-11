# ADR-0024: Campos informativos exigidos por template

**Status**: Proposto

**Data**: 2026-11-10

**Decisores**: Equipe Intelicity

**Tags**: template, formulário, campos informativos, contrato, validação

## Contexto

O template define seções para o executor preencher, mas não tem como exigir dados de quem **cria** o formulário (foto de evidência, observação do gestor, localização). Hoje `information_fields` entra no `POST /forms` sem nenhuma regra: o template não sabe o que esperar e o formulário nasce sem o dado.

O front (web e app) cria formulários e edita templates; qualquer exigência nova só funciona se os dois lados usarem o mesmo contrato.

## Decisão

- O template ganha `information_fields`: lista de definições `{key, label, information_field_type, required, file_type?}`. A `key` é única no template. `file_type` (`IMAGE` ou `DOCUMENT`) só existe para campo de arquivo.
- Cada campo informativo do formulário pode trazer `key`. O `POST /forms` confere os campos enviados contra as definições do template: obrigatório ausente, `key` repetida, tipo divergente, arquivo sem declaração e categoria de arquivo incompatível com o mimetype retornam `EntityError` (400).
- A regra mora no domínio: `TemplateInformationField` (a exigência) e `Template.validate_information_fields` (a conferência). O usecase só chama.
- Alterar as definições de um template em uso conta como mudança de conteúdo e exige `new_version: true` (versionamento já existente). Formulários existentes não mudam; propagar seções não toca os dados informativos.
- Persistência: atributo `information_fields` no item do template e `key` no campo informativo do formulário. Os dois são opcionais.
- O arquivo é só **declarado** no `POST`: o upload segue como segunda operação (PUT na URL pré-assinada). A validação não prova que os bytes existem.

## Consequências

- Template e formulário gravados antes continuam válidos: sem `information_fields` não há exigência, e campo sem `key` não atende exigência alguma.
- **Risco de rollout:** ativar uma definição obrigatória num template cujo cliente ainda não envia `key` faz toda criação daquele template falhar. Ativar só depois de confirmar o cliente.
- Campo informativo sem `key` continua aceito mesmo quando o template tem exigências, para não quebrar integrações existentes (ex.: sync de origem).
- A confirmação do upload (bytes no S3) continua fora do `POST`; é tratada pela recuperação e reconciliação de uploads (ADR-0019).
- Os clientes precisam implementar a edição das definições e o envio das `key`. O contrato está em `docs/campos-informativos-template.md`.

## Alternativas consideradas

- **Obrigatoriedade como campo de seção do template**: descartada. Seção é do executor e é copiada para o formulário; o dado do criador tem outro dono e outro momento.
- **Validar só no front**: descartada. O sync e as integrações criam formulários sem passar pelo front.
- **Rejeitar campo informativo sem `key` quando há exigências**: descartada por quebrar integrações existentes sem ganho; a exigência já falha se a `key` obrigatória faltar.
