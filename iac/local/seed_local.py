#!/usr/bin/env python3
"""Dados de exemplo para o ambiente local.

Cria, para o usuário local (o mesmo que o modo de login local do front usa):
  - GAIA: OS próprias em Pendente, Em andamento e Completo;
  - UBERLANDIA: OS em aberto no pool, com foto no campo informativo, e a
    `SystemConfig` que libera OS sem dono (`allow_unassigned_forms`);
  - um template por sistema, com campo de foto para exercitar o upload no S3.

Ids fixos: rodar de novo não duplica nada — o que já existe é pulado. Para
recomeçar do zero: `bootstrap_local.py --reset-db --seed`.

O perfil do usuário não entra aqui: o `POST /profiles/login` cria um INSPECTOR
na primeira chamada, como na AWS.
"""
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
from src.shared.domain.entities.section import Section  # noqa: E402
from src.shared.domain.entities.system_config import SystemConfig  # noqa: E402
from src.shared.domain.entities.template import Template  # noqa: E402
from src.shared.domain.enums.file_type_enum import FileType  # noqa: E402
from src.shared.domain.enums.form_origin_enum import FormOrigin  # noqa: E402
from src.shared.domain.enums.form_status_enum import FormStatus  # noqa: E402
from src.shared.domain.enums.priority_enum import Priority  # noqa: E402
from src.shared.environments import Environments  # noqa: E402
from src.shared.helpers.functions.s3_url import build_s3_url  # noqa: E402

# Mesmo usuário do modo de login local do front (clients/web/src/lib/local-auth.ts).
# 36 caracteres, como um `sub` do Cognito — a entidade Form valida o tamanho.
LOCAL_USER_ID = "10ca1000-0000-4000-8000-000000000001"

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
    s3.put_object(Bucket=envs.bucket_name, Key=key, Body=_png(rgb), ContentType="image/png")
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


def seed_system_config() -> None:
    repo = Environments.get_system_config_repo()
    current = repo.get_by_system("UBERLANDIA")
    now = _now()
    repo.put(SystemConfig(
        system="UBERLANDIA",
        created_at=current.created_at if current else now,
        updated_at=now,
        scope_keys=current.scope_keys if current else None,
        scope_partition_key=current.scope_partition_key if current else None,
        geofence_radius_m=current.geofence_radius_m if current else None,
        allow_unassigned_forms=True,
    ))
    print("[ok]   SystemConfig UBERLANDIA (allow_unassigned_forms)")


def _justification() -> Justification:
    # Motivos de cancelamento: chegam por OS no `POST /forms`, como na AWS.
    return Justification(options=[
        JustificationOption(option="Local inacessível", required_image=True, required_text=False),
        JustificationOption(option="Serviço já executado", required_image=True, required_text=False),
        JustificationOption(option="Outro motivo", required_image=False, required_text=True),
    ])


def _form(key: str, template: Template, **overrides) -> Form:
    now = _now()
    base = dict(
        id=_id(f"form:{key}"), created_by=LOCAL_USER_ID, user_id=LOCAL_USER_ID,
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

    forms = [
        _form("gaia-pendente", gaia, form_title="Vistoria de ramal — Rua Augusta",
              street="Rua Augusta, 500", city="São Paulo", latitude=-23.5534, longitude=-46.6575),
        _form("gaia-em-andamento", gaia, form_title="Vistoria de ramal — Av. Paulista",
              street="Av. Paulista, 1000", city="São Paulo", latitude=-23.5631, longitude=-46.6544,
              status=FormStatus.IN_PROGRESS, in_progress_at=now, priority=Priority.HIGH),
        _form("gaia-completo", gaia, form_title="Vistoria de ramal — Rua da Consolação",
              street="Rua da Consolação, 2000", city="São Paulo", latitude=-23.5560, longitude=-46.6620,
              status=FormStatus.COMPLETED, in_progress_at=now, completed_at=now, completed_by=LOCAL_USER_ID),
    ]

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
        if repo.get_form_by_id(user_id=LOCAL_USER_ID, form_id=form.id):
            print(f"[skip] {form.form_title}")
            continue
        repo.create_form(form)
        print(f"[ok]   {form.form_title} ({form.system}, {form.status.value})")


def main() -> int:
    templates = seed_templates()
    seed_system_config()
    seed_forms(templates)
    print("\n[ok] Seed concluído. Usuário local:", LOCAL_USER_ID)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
