from dataclasses import dataclass
from typing import Any

try:
    from boto3.dynamodb.conditions import Attr, Key
except ImportError:
    @dataclass(frozen=True)
    class _ConditionExpression:
        operator: str
        name: str | None = None
        value: Any = None
        second_value: Any = None
        left: Any = None
        right: Any = None

        def __and__(self, other: Any) -> "_ConditionExpression":
            return _ConditionExpression(operator="AND", left=self, right=other)

        def __or__(self, other: Any) -> "_ConditionExpression":
            return _ConditionExpression(operator="OR", left=self, right=other)


    class _ConditionBuilder:
        def __init__(self, name: str):
            self.name = name

        def _build(self, operator: str, value: Any = None, second_value: Any = None) -> _ConditionExpression:
            return _ConditionExpression(
                operator=operator,
                name=self.name,
                value=value,
                second_value=second_value,
            )

        def eq(self, value: Any) -> _ConditionExpression:
            return self._build("EQ", value=value)

        def begins_with(self, value: Any) -> _ConditionExpression:
            return self._build("BEGINS_WITH", value=value)

        def contains(self, value: Any) -> _ConditionExpression:
            return self._build("CONTAINS", value=value)

        def between(self, low: Any, high: Any) -> _ConditionExpression:
            return self._build("BETWEEN", value=low, second_value=high)

        def gte(self, value: Any) -> _ConditionExpression:
            return self._build("GTE", value=value)

        def lte(self, value: Any) -> _ConditionExpression:
            return self._build("LTE", value=value)


    class Key(_ConditionBuilder):
        pass


    class Attr(_ConditionBuilder):
        pass
