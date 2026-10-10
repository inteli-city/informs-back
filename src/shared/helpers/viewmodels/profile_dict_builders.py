from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.services.access_control import SystemAccess


def build_profile_dict(profile: Profile) -> dict:
    return {
        "user_id": profile.user_id,
        "name": profile.name,
        "email": profile.email,
        "active": profile.active,
        "super_admin": profile.super_admin,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


def build_system_access_dict(access: SystemAccess) -> dict:
    return {
        "system": access.system,
        "role_id": access.role_id,
        "role_name": access.role_name,
        # Ordenado para a resposta ser estável (frozenset não tem ordem).
        "actions": sorted(action.value for action in access.actions),
    }


def build_system_role_dict(role: SystemRole) -> dict:
    return {
        "system": role.system,
        "role_id": role.role_id,
        "name": role.name,
        "actions": [action.value for action in role.actions],
        "is_default": role.is_default,
        "fixed": False,
    }
