from typing import List

from src.shared.domain.enums.action_enum import ACTION_DESCRIPTIONS, Action
from src.shared.helpers.contracts.endpoints.system_access_contract import GetPermissionActionsResponseSchema


class GetPermissionActionsViewmodel:
    def __init__(self, actions: List[Action]):
        self.actions = actions

    def to_dict(self) -> dict:
        payload = {
            "actions": [
                {"action": action.value, "description": ACTION_DESCRIPTIONS[action]}
                for action in self.actions
            ],
        }
        return GetPermissionActionsResponseSchema.model_validate(payload).model_dump()
