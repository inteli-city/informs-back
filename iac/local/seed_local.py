#!/usr/bin/env python3
"""Dados de exemplo para o ambiente local.

Contas (as mesmas do seletor do login local do front, em
`clients/web/src/lib/local-auth.ts` — mudar aqui exige mudar lá):
  - Uberlândia: só UBERLANDIA, ADMIN do sistema;
  - GAIA: só GAIA, Técnico (papel padrão: só percurso);
  - Gestor GAIA: só GAIA, Gestor (pessoas e templates, sem ser ADMIN);
  - GAIA + Uberlândia: os dois sistemas, super admin.

Com o RBAC por sistema (ADR-0020) o seed cria também os papéis Técnico e
Gestor em cada sistema e o vínculo de cada conta. No modelo antigo (role
global), grava `role`/`admin_systems` como antes.

Dados:
  - GAIA: OS próprias em Pendente, Em andamento e Completo, para cada conta
    que tem GAIA;
  - UBERLANDIA: OS em aberto no pool (vistas por toda conta de Uberlândia),
    com foto no campo informativo, a `SystemConfig` que libera OS sem dono
    (`allow_unassigned_forms`) e uma OS já atribuída à conta de Uberlândia;
  - um template por sistema, com campo de foto para exercitar o upload no S3.

Ids fixos: rodar de novo não duplica nada — o que já existe é pulado (os
perfis são reescritos, para o papel valer mesmo se o login já tiver criado o
perfil como INSPECTOR). Para recomeçar do zero:
`bootstrap_local.py --reset-db --seed`.
"""
import inspect
import struct
import sys
import time
import uuid
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_env  # noqa: E402,F401  (precisa vir antes de qualquer src.*)

import boto3  # noqa: E402

from src.shared.domain.entities.field import DropDownField, FileField, TextField  # noqa: E402
from src.shared.domain.entities.form import Form  # noqa: E402
from src.shared.domain.entities.information_field import TextInformationField, UrlInformationField  # noqa: E402
from src.shared.domain.entities.justification import Justification, JustificationOption  # noqa: E402
from src.shared.domain.entities.profile import Profile  # noqa: E402
from src.shared.domain.entities.section import Section  # noqa: E402
from src.shared.domain.entities.system_config import SystemConfig  # noqa: E402
from src.shared.domain.entities.template import Template  # noqa: E402
from src.shared.domain.enums.file_type_enum import FileType  # noqa: E402
from src.shared.domain.enums.form_origin_enum import FormOrigin  # noqa: E402
from src.shared.domain.enums.form_status_enum import FormStatus  # noqa: E402
from src.shared.domain.enums.priority_enum import Priority  # noqa: E402
from src.shared.environments import Environments  # noqa: E402
from src.shared.helpers.functions.s3_url import build_s3_url  # noqa: E402

# `sub` com 36 caracteres, como no Cognito — a entidade Form valida o tamanho.
# A conta dos dois sistemas mantém o id do antigo usuário único, para quem já
# tem dados locais não perdê-los.
BOTH_USER_ID = "10ca1000-0000-4000-8000-000000000001"
UBERLANDIA_USER_ID = "10ca1000-0000-4000-8000-000000000002"
GAIA_USER_ID = "10ca1000-0000-4000-8000-000000000003"
GESTOR_GAIA_USER_ID = "10ca1000-0000-4000-8000-000000000004"
LOCAL_USER_ID = BOTH_USER_ID  # dono dos templates
SAO_PAULO = "São Paulo"

# `roles`: papel por sistema (RBAC). `legacy_role`/`admin_systems`: o mesmo
# acesso no modelo antigo, para o seed seguir rodando antes do RBAC.
LOCAL_ACCOUNTS = [
    dict(user_id=UBERLANDIA_USER_ID, name="Campo Uberlândia", email="uberlandia@informs.local",
         systems=["UBERLANDIA"], super_admin=False, roles={"UBERLANDIA": "ADMIN"},
         legacy_role="INSPECTOR", admin_systems=["UBERLANDIA"]),
    dict(user_id=GAIA_USER_ID, name="Campo GAIA", email="gaia@informs.local",
         systems=["GAIA"], super_admin=False, roles={"GAIA": "tecnico"},
         legacy_role="INSPECTOR", admin_systems=[]),
    dict(user_id=GESTOR_GAIA_USER_ID, name="Gestor GAIA", email="gestor@informs.local",
         systems=["GAIA"], super_admin=False, roles={"GAIA": "gestor"},
         legacy_role="INSPECTOR", admin_systems=["GAIA"]),
    dict(user_id=BOTH_USER_ID, name="Dev Local", email="dev@informs.local",
         systems=["GAIA", "UBERLANDIA"], super_admin=True, roles={"GAIA": "tecnico", "UBERLANDIA": "tecnico"},
         legacy_role="ADMIN", admin_systems=[]),
]

# Papéis criados em cada sistema (RBAC). ADMIN é o papel fixo do back-end.
LOCAL_ROLES = {
    "tecnico": dict(name="Técnico", is_default=True, actions=["tracking.start"]),
    "gestor": dict(name="Gestor", is_default=False, actions=[
        "forms.view_all", "forms.assign", "forms.release", "tracking.start", "tracking.view",
        "users.manage", "templates.manage",
    ]),
}

_NAMESPACE = uuid.UUID("6f1c2a52-7d1e-4c55-9a43-1b0d5e2f9c11")


def _id(name: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, name))


def _now() -> int:
    return int(time.time() * 1000)


def _png(rgb: tuple, size: int = 64) -> bytes:
    """PNG de cor sólida, sem depender de Pillow."""
    raw = b"".join(b"\x00" + bytes(rgb) * size for _ in range(size))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _upload_image(key: str, rgb: tuple) -> str:
    envs = Environments.get_envs()
    s3 = boto3.client("s3", endpoint_url=envs.s3_endpoint_url, region_name=envs.region)
    s3.put_object(
        Bucket=envs.bucket_name, Key=key, Body=_png(rgb), ContentType="image/png",
        ExpectedBucketOwner=local_env.LOCALSTACK_ACCOUNT_ID,
    )
    return build_s3_url(key)


def _sections() -> list:
    return [
        Section(section_id=1, fields=[
            TextField(label="Responsável no local", required=True, key="responsavel", order=1),
            DropDownField(label="Situação encontrada", required=True, key="situacao", order=2,
                          options=["Conforme", "Com avaria", "Inacessível"]),
        ]),
        Section(section_id=2, fields=[
            FileField(label="Foto do serviço", required=True, key="foto", order=1,
                      file_type=FileType.IMAGE, min_quantity=1, max_quantity=3),
            TextField(label="Observações", required=False, key="observacoes", order=2),
        ]),
    ]


def seed_templates() -> dict:
    repo = Environments.get_template_repo()
    templates = {}
    for system, name in (("GAIA", "Vistoria de ramal (local)"), ("UBERLANDIA", "Recuperação asfáltica (local)")):
        template_id = _id(f"template:{system}")
        existing = repo.get_template(template_id)
        if existing:
            print(f"[skip] template {name}")
            templates[system] = existing
            continue
        now = _now()
        template = Template(
            id=template_id, name=name, system=system, description="Criado pelo seed local",
            is_active=True, created_by=LOCAL_USER_ID, created_at=now, updated_at=now, sections=_sections(),
        )
        templates[system] = repo.create_template(template)
        print(f"[ok]   template {name}")
    return templates


def _supports(fn, name: str) -> bool:
    # `admin_systems` só existe a partir de feature/config-fase-4; nas branches
    # anteriores o seed segue funcionando, sem o admin por sistema.
    return name in inspect.signature(fn).parameters


def _is_rbac() -> bool:
    # RBAC por sistema (ADR-0020): o perfil tem `super_admin` e não tem `role`.
    return _supports(Profile.__init__, "super_admin")


def seed_profiles() -> None:
    if _is_rbac():
        _seed_profiles_rbac()
    else:
        _seed_profiles_legacy()


def _seed_profiles_legacy() -> None:
    from src.shared.domain.enums.profile_role_enum import ProfileRole

    repo = Environments.get_profile_repo()
    for account in LOCAL_ACCOUNTS:
        now = _now()
        role = ProfileRole(account["legacy_role"])
        admin_systems = account["admin_systems"]
        current = repo.get_by_user_id(account["user_id"])
        if current is None:
            kwargs = dict(
                user_id=account["user_id"], role=role, name=account["name"], email=account["email"],
                system=account["systems"][0], active=True, created_at=now, updated_at=now,
            )
            if _supports(Profile.__init__, "admin_systems"):
                kwargs["admin_systems"] = admin_systems
            repo.create(Profile(**kwargs))
        else:
            kwargs = dict(user_id=account["user_id"], role=role, updated_at=now)
            if _supports(repo.update_profile, "admin_systems"):
                kwargs["admin_systems"] = admin_systems
            repo.update_profile(**kwargs)
        admin = f", administra {', '.join(admin_systems)}" if admin_systems else ""
        print(f"[ok]   perfil {account['email']} ({role.value}{admin})")


def _seed_profiles_rbac() -> None:
    from src.shared.domain.entities.system_membership import SystemMembership
    from src.shared.domain.entities.system_role import SystemRole
    from src.shared.domain.enums.action_enum import Action
    from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO

    profiles = Environments.get_profile_repo()
    roles = Environments.get_system_role_repo()
    now = _now()

    # Papéis com ids fixos: rodar de novo regrava o mesmo papel. Um papel padrão
    # por sistema — se já houver outro (ex.: criado pela migração), o nosso não
    # disputa a marca.
    for system in sorted({system for account in LOCAL_ACCOUNTS for system in account["systems"]}):
        existing = {role.role_id: role for role in roles.list_roles(system)}
        other_default = any(role.is_default for role_id, role in existing.items() if role_id not in LOCAL_ROLES)
        for role_id, spec in LOCAL_ROLES.items():
            current = existing.get(role_id)
            roles.put_role(SystemRole(
                system=system, role_id=role_id, name=spec["name"],
                actions=[Action(action) for action in spec["actions"]],
                is_default=spec["is_default"] and not other_default,
                created_at=current.created_at if current else now, updated_at=now,
            ))
        print(f"[ok]   papéis em {system}: {', '.join(spec['name'] for spec in LOCAL_ROLES.values())}")

    for account in LOCAL_ACCOUNTS:
        current = profiles.get_by_user_id(account["user_id"])
        person = Profile(
            user_id=account["user_id"], name=account["name"], email=account["email"], active=True,
            created_at=current.created_at if current else now, updated_at=now,
            super_admin=account["super_admin"],
        )
        # Grava a pessoa por cima (sem a condição do `create`): também limpa um
        # perfil local ainda no formato antigo (`role`, `system`, ...).
        profiles.dynamo.put_item(
            item=ProfileDynamoDTO.from_entity(person).to_dynamo(),
            partition_key=ProfileDynamoDTO.build_pk(person.user_id),
            sort_key=ProfileDynamoDTO.build_sk(),
        )
        for system, role_id in account["roles"].items():
            profiles.put_membership(SystemMembership(
                user_id=account["user_id"], system=system, role_id=role_id, created_at=now, updated_at=now,
            ))
        access = ", ".join(f"{system}: {role_id}" for system, role_id in account["roles"].items())
        print(f"[ok]   perfil {account['email']} ({'super admin; ' if account['super_admin'] else ''}{access})")


def seed_system_config() -> None:
    repo = Environments.get_system_config_repo()
    current = repo.get_by_system("UBERLANDIA")
    now = _now()
    kwargs = dict(
        system="UBERLANDIA",
        created_at=current.created_at if current else now,
        updated_at=now,
        scope_keys=current.scope_keys if current else None,
        scope_partition_key=current.scope_partition_key if current else None,
        geofence_radius_m=current.geofence_radius_m if current else None,
        allow_unassigned_forms=True,
    )
    # O `put` grava o item inteiro: sem repassar a camada de configuração do
    # sistema (feature/config-*), rodar o seed de novo apagaria o que foi
    # configurado no Admin.
    for field in ("app_config", "app_config_version"):
        if current is not None and _supports(SystemConfig.__init__, field):
            kwargs[field] = getattr(current, field)
    repo.put(SystemConfig(**kwargs))
    print("[ok]   SystemConfig UBERLANDIA (allow_unassigned_forms)")


def _justification() -> Justification:
    # Motivos de cancelamento: chegam por OS no `POST /forms`, como na AWS.
    return Justification(options=[
        JustificationOption(option="Local inacessível", required_image=True, required_text=False),
        JustificationOption(option="Serviço já executado", required_image=True, required_text=False),
        JustificationOption(option="Outro motivo", required_image=False, required_text=True),
    ])


def _form(key: str, template: Template, owner: str = BOTH_USER_ID, **overrides) -> Form:
    now = _now()
    base = dict(
        id=_id(f"form:{key}"), created_by=owner, user_id=owner,
        template=template.id, system=template.system, sections=_sections(),
        priority=Priority.MEDIUM, status=FormStatus.PENDING, created_at=now, updated_at=now,
        justification=_justification(),
    )
    base.update(overrides)
    return Form(**base)


def seed_forms(templates: dict) -> None:
    repo = Environments.get_form_repo()
    gaia, uberlandia = templates["GAIA"], templates["UBERLANDIA"]
    now = _now()

    forms = []
    # Os mesmos três estados de GAIA para cada conta que tem GAIA. A conta dos
    # dois sistemas mantém as chaves antigas (ids já existentes).
    for owner, prefix, offset in ((BOTH_USER_ID, "gaia", 0), (GAIA_USER_ID, "gaia-only", 50)):
        forms += [
            _form(f"{prefix}-pendente", gaia, owner=owner,
                  form_title=f"Vistoria de ramal — Rua Augusta, {500 + offset}",
                  street=f"Rua Augusta, {500 + offset}", city=SAO_PAULO,
                  latitude=-23.5534, longitude=-46.6575 + offset / 10000),
            _form(f"{prefix}-em-andamento", gaia, owner=owner,
                  form_title=f"Vistoria de ramal — Av. Paulista, {1000 + offset}",
                  street=f"Av. Paulista, {1000 + offset}", city=SAO_PAULO,
                  latitude=-23.5631, longitude=-46.6544 + offset / 10000,
                  status=FormStatus.IN_PROGRESS, in_progress_at=now, priority=Priority.HIGH),
            _form(f"{prefix}-completo", gaia, owner=owner,
                  form_title=f"Vistoria de ramal — Rua da Consolação, {2000 + offset}",
                  street=f"Rua da Consolação, {2000 + offset}", city=SAO_PAULO,
                  latitude=-23.5560, longitude=-46.6620 + offset / 10000,
                  status=FormStatus.COMPLETED, in_progress_at=now, completed_at=now, completed_by=owner),
        ]

    # Uma OS já com dono para a conta de Uberlândia, além do pool.
    forms.append(_form(
        "ube-atribuida", uberlandia, owner=UBERLANDIA_USER_ID,
        form_title="OS #2607000010 - RECUPERAÇÃO ASFÁLTICA", street="Av. Rondon Pacheco, 1500",
        city="Uberlândia", latitude=-18.9130, longitude=-48.2700, external_id="#2607000010",
        origin=FormOrigin.AI, service_type="RECUPERACAO_ASFALTICA",
    ))

    pool = [
        ("ube-pool-1", "OS #2607000001 - RECUPERAÇÃO ASFÁLTICA", "Rua Afif Attiê, 0", -18.9168, -48.3206, (210, 70, 60)),
        ("ube-pool-2", "OS #2607000002 - RECUPERAÇÃO ASFÁLTICA", "Av. João Naves de Ávila, 3333", -18.9186, -48.2580, (60, 120, 200)),
        ("ube-pool-3", "OS #2607000003 - RECUPERAÇÃO ASFÁLTICA", "Rua Santa Edwiges, 434", -18.9010, -48.2900, (90, 160, 80)),
    ]
    for key, title, street, lat, lng, color in pool:
        image_url = _upload_image(f"seed/{key}.png", color)
        forms.append(_form(
            key, uberlandia, form_title=title, street=street, city="Uberlândia", latitude=lat, longitude=lng,
            user_id=None, external_id=title.split(" ")[1], origin=FormOrigin.AI, service_type="RECUPERACAO_ASFALTICA",
            information_fields=[
                TextInformationField(value=f"Recuperação asfáltica no endereço {street}."),
                UrlInformationField(url=image_url, mimetype="image/png"),
            ],
        ))

    for form in forms:
        if repo.get_form_by_id(user_id=form.user_id or BOTH_USER_ID, form_id=form.id):
            print(f"[skip] {form.form_title}")
            continue
        repo.create_form(form)
        print(f"[ok]   {form.form_title} ({form.system}, {form.status.value})")


def main() -> int:
    seed_profiles()
    templates = seed_templates()
    seed_system_config()
    seed_forms(templates)
    print("\n[ok] Seed concluído. Contas:")
    for account in LOCAL_ACCOUNTS:
        print(f"       {account['email']:<26} {', '.join(account['systems'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
