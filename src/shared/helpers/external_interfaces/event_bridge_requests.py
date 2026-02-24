from typing import Any, Dict, List, Optional

from src.shared.helpers.external_interfaces.external_interface import IRequest


class LambdaEventBridgeRequest(IRequest):
    event_id: Optional[str]
    source: Optional[str]
    detail_type: Optional[str]
    time: Optional[str]
    region: Optional[str]
    account: Optional[str]
    resources: List[str]
    detail: Dict[str, Any]
    version: Optional[str]
    replay_name: Optional[str]

    def __init__(self, event: Dict[str, Any] = None) -> None:
        self.raw_event = event or {}
        self.event_id = self.raw_event.get("id")
        self.source = self.raw_event.get("source")
        self.detail_type = self.raw_event.get("detail-type")
        self.time = self.raw_event.get("time")
        self.region = self.raw_event.get("region")
        self.account = self.raw_event.get("account")
        self.resources = self.raw_event.get("resources") or []
        self.detail = self.raw_event.get("detail") or {}
        self.version = self.raw_event.get("version")
        self.replay_name = self.raw_event.get("replay-name")

    @property
    def data(self) -> Dict[str, Any]:
        return self.raw_event

    def summary(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "detail_type": self.detail_type,
            "time": self.time,
            "region": self.region,
            "account": self.account,
            "resources": self.resources,
        }

    def __repr__(self) -> str:
        return (
            "LambdaEventBridgeRequest("
            f"event_id={self.event_id}, source={self.source}, detail_type={self.detail_type}, "
            f"time={self.time}, region={self.region}, account={self.account})"
        )
