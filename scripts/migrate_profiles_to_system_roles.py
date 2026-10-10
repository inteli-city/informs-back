"""Migra a tabela Profiles do role global para roles por sistema.

Antes: um item por pessoa com `role` (ADMIN/INSPECTOR/MANAGER/SUPERVISOR),
`system`, `scope` e `vehicle_plate`, indexado por `GSI1PK = role#{role}`.

Depois (ver src/shared/infra/dtos/):
    user#{id}     / METADATA        pessoa: name, email, active, super_admin
    user#{id}     / system#{system} vínculo: role_id
    system#{sys}  / role#{role_id}  role do sistema: name, actions, is_default

O que o script faz, por sistema encontrado nos perfis (e os de --system):
  1. Cria os roles equivalentes aos papéis de antes:
       INSPECTOR  → "Técnico" (tracking.start) — vira o role padrão
       MANAGER    → "Gestor"  (forms.view_all, forms.assign, forms.release)
       SUPERVISOR → "Fiscal"  (as mesmas do Gestor)
     Gestor e Fiscal só são criados onde alguém tinha esses papéis.
  2. Cria o vínculo de cada pessoa com o `system` dela: ADMIN vira o role
     fixo ADMIN do sistema; os outros, o role equivalente.
  3. Limpa o item da pessoa: tira role, system, scope, vehicle_plate e o
     GSI1 antigo; grava super_admin (true para os --super-admin).
  4. Dá o role ADMIN nos sistemas pedidos em --system-admin. O ADMIN de antes
     vira ADMIN só no `system` gravado no perfil (o primeiro grupo do
     Cognito), que pode não ser o sistema em que a conta precisa administrar
     — ex.: a conta de integração que cria as OS de UBERLANDIA.

Idempotente: role e vínculo que já existem não são regravados; pessoa já
migrada (sem `role`) não ganha vínculo de novo.

Uso (mesmas variáveis de ambiente das Lambdas):

    AWS_PROFILE=intelicity REGION=sa-east-1 \\
    DYNAMO_PROFILE_TABLE_NAME=FormulariosStackdev-...ProfilesTable... \\
    python scripts/migrate_profiles_to_system_roles.py --super-admin <user_id> \\
        --system-admin <user_id>:UBERLANDIA --dry-run
"""

import argparse
import os
import sys
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple

import boto3
from boto3.dynamodb.conditions import Attr


TECNICO = ("tecnico", "Técnico", ["tracking.start"])
GESTOR = ("gestor", "Gestor", ["forms.view_all", "forms.assign", "forms.release"])
FISCAL = ("fiscal", "Fiscal", ["forms.view_all", "forms.assign", "forms.release"])

ROLE_FOR = {"INSPECTOR": TECNICO, "MANAGER": GESTOR, "SUPERVISOR": FISCAL}
ADMIN_ROLE_ID = "ADMIN"
LEGACY_FIELDS = ["role", "system", "scope", "vehicle_plate", "GSI1PK", "GSI1SK"]


def _scan_people(table) -> List[dict]:
    items, kwargs = [], {"FilterExpression": Attr("SK").eq("METADATA")}
    while True:
        resp = table.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            return items
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]


def _exists(table, pk: str, sk: str) -> bool:
    return "Item" in table.get_item(Key={"PK": pk, "SK": sk})


def _put(table, item: dict, dry_run: bool, label: str) -> None:
    print(f"  + {label}")
    if not dry_run:
        table.put_item(Item=item)


def _ensure_role(table, system: str, role, is_default: bool, now: int, dry_run: bool) -> None:
    role_id, name, actions = role
    if _exists(table, f"system#{system}", f"role#{role_id}"):
        return
    _put(table, {
        "PK": f"system#{system}", "SK": f"role#{role_id}",
        "system": system, "role_id": role_id, "name": name, "actions": actions,
        "is_default": is_default, "created_at": now, "updated_at": now,
    }, dry_run, f"role {system}/{name}{' (padrão)' if is_default else ''}")


def _ensure_membership(table, user_id: str, system: str, role_id: str, now: int, dry_run: bool) -> None:
    if _exists(table, f"user#{user_id}", f"system#{system}"):
        return
    _put(table, {
        "PK": f"user#{user_id}", "SK": f"system#{system}",
        "user_id": user_id, "system": system, "role_id": role_id, "created_at": now, "updated_at": now,
        "GSI1PK": f"system#{system}", "GSI1SK": f"role#{role_id}#user#{user_id}",
    }, dry_run, f"vínculo {user_id} → {system}/{role_id}")


def _clean_person(table, person: dict, super_admin: bool, dry_run: bool) -> None:
    user_id = person["PK"].split("user#", 1)[1]
    to_set = {"super_admin": super_admin}
    to_remove = [field for field in LEGACY_FIELDS if field in person]
    if super_admin:
        # Índice esparso: só super admin tem GSI1 no item da pessoa.
        to_set.update({"GSI1PK": "super_admin", "GSI1SK": f"user#{user_id}"})
        to_remove = [field for field in to_remove if field not in to_set]
    if not to_remove and all(person.get(field) == value for field, value in to_set.items()):
        return

    print(f"  ~ pessoa {user_id}: super_admin={super_admin}; remove {to_remove or '-'}")
    if dry_run:
        return
    names, values, set_parts, remove_parts = {}, {}, [], []
    for i, (field, value) in enumerate(to_set.items()):
        names[f"#s{i}"], values[f":s{i}"] = field, value
        set_parts.append(f"#s{i} = :s{i}")
    for i, field in enumerate(to_remove):
        names[f"#r{i}"] = field
        remove_parts.append(f"#r{i}")
    expression = "SET " + ", ".join(set_parts)
    if remove_parts:
        expression += " REMOVE " + ", ".join(remove_parts)
    table.update_item(
        Key={"PK": person["PK"], "SK": "METADATA"},
        UpdateExpression=expression,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def _ensure_admin_membership(table, user_id: str, system: str, now: int, dry_run: bool) -> None:
    """Como _ensure_membership, mas troca um vínculo que já existe com outro
    role: aqui o pedido explícito vale mais que o papel de antes."""
    if not _exists(table, f"user#{user_id}", "METADATA"):
        print(f"  ! {user_id} não tem perfil: entre no app uma vez e rode de novo")
        return
    current = table.get_item(Key={"PK": f"user#{user_id}", "SK": f"system#{system}"}).get("Item")
    if current and current.get("role_id") == ADMIN_ROLE_ID:
        return
    _put(table, {
        "PK": f"user#{user_id}", "SK": f"system#{system}",
        "user_id": user_id, "system": system, "role_id": ADMIN_ROLE_ID,
        "created_at": current["created_at"] if current else now, "updated_at": now,
        "GSI1PK": f"system#{system}", "GSI1SK": f"role#{ADMIN_ROLE_ID}#user#{user_id}",
    }, dry_run, f"vínculo {user_id} → {system}/{ADMIN_ROLE_ID} (--system-admin)")


def _parse_system_admin(value: str) -> Tuple[str, str]:
    user_id, sep, system = value.partition(":")
    if not sep or not user_id.strip() or not system.strip():
        raise argparse.ArgumentTypeError(f"use <user_id>:<SISTEMA> (recebido: {value!r})")
    return user_id.strip(), system.strip()


def migrate(
    table, super_admins: Set[str], extra_systems: List[str], dry_run: bool,
    system_admins: Iterable[Tuple[str, str]] = (),
) -> None:
    people = _scan_people(table)
    now = int(time.time() * 1000)

    legacy_roles_by_system: Dict[str, Set[str]] = {system: set() for system in extra_systems}
    for person in people:
        if person.get("system") and person.get("role"):
            legacy_roles_by_system.setdefault(person["system"], set()).add(person["role"])

    print(f"{len(people)} pessoa(s); sistemas: {sorted(legacy_roles_by_system) or '-'}")
    for system, legacy_roles in sorted(legacy_roles_by_system.items()):
        print(f"[{system}]")
        _ensure_role(table, system, TECNICO, is_default=True, now=now, dry_run=dry_run)
        for legacy, role in (("MANAGER", GESTOR), ("SUPERVISOR", FISCAL)):
            if legacy in legacy_roles:
                _ensure_role(table, system, role, is_default=False, now=now, dry_run=dry_run)

    print("[pessoas]")
    for person in people:
        user_id = person["PK"].split("user#", 1)[1]
        role: Optional[str] = person.get("role")
        system: Optional[str] = person.get("system")
        if role and system:
            role_id = ADMIN_ROLE_ID if role == "ADMIN" else ROLE_FOR[role][0]
            _ensure_membership(table, user_id, system, role_id, now, dry_run)
        _clean_person(table, person, super_admin=user_id in super_admins or bool(person.get("super_admin")), dry_run=dry_run)

    known = {person["PK"].split("user#", 1)[1] for person in people}
    for user_id in sorted(super_admins - known):
        print(f"  ! --super-admin {user_id} não tem perfil: entre no app uma vez e rode de novo")

    if system_admins:
        print("[--system-admin]")
    for user_id, system in system_admins:
        _ensure_admin_membership(table, user_id, system, now, dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra a tabela Profiles para roles por sistema")
    parser.add_argument("--super-admin", action="append", default=[], help="user_id a marcar como super admin (repetível)")
    parser.add_argument("--system", action="append", default=[], help="Sistema sem perfis que também deve ganhar o role padrão (repetível)")
    parser.add_argument(
        "--system-admin", action="append", default=[], type=_parse_system_admin,
        help="<user_id>:<SISTEMA> que recebe o role ADMIN no sistema (repetível)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que mudaria, sem gravar")
    args = parser.parse_args()

    table_name = os.environ.get("DYNAMO_PROFILE_TABLE_NAME")
    if not table_name:
        raise SystemExit("DYNAMO_PROFILE_TABLE_NAME precisa estar definido")
    region = os.environ.get("REGION") or os.environ.get("AWS_REGION", "sa-east-1")
    table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    print(f"Tabela: {table_name}{' (dry-run)' if args.dry_run else ''}")
    migrate(table, set(args.super_admin), args.system, args.dry_run, system_admins=args.system_admin)
    if args.dry_run:
        print("--dry-run: nada foi gravado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
