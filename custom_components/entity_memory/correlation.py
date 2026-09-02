"""Correlate Home Assistant service calls with resulting state changes."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Context, Event

from .const import SIGNIFICANT_ATTRIBUTES
from .models import EventOrigin, MemoryEvent, classify_origin

CORRELATION_TIMEOUT = timedelta(seconds=180)


@dataclass(slots=True, frozen=True)
class ServiceIntent:
    """A command expected to cause a later entity state change."""

    entity_id: str
    timestamp: datetime
    service: str
    expected: dict[str, Any]
    origin: EventOrigin
    context_id: str | None
    parent_id: str | None
    user_id: str | None


def _entity_ids(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _expected_values(domain: str, service: str, data: dict[str, Any]) -> dict[str, Any]:
    """Translate a standard service call into observable entity values."""
    expected: dict[str, Any] = {}
    if service == "turn_on":
        expected["state"] = "on"
    elif service == "turn_off":
        expected["state"] = "off"
    elif domain == "cover" and service == "open_cover":
        expected["state"] = "open"
    elif domain == "cover" and service == "close_cover":
        expected["state"] = "closed"
    elif domain == "climate" and "hvac_mode" in data:
        expected["state"] = data["hvac_mode"]

    attribute_names = set(SIGNIFICANT_ATTRIBUTES.get(domain, ()))
    if domain == "cover":
        attribute_names.add("position")
    if domain == "climate":
        attribute_names.discard("hvac_mode")
    for name in attribute_names:
        if not name or name not in data:
            continue
        target_name = "current_position" if name == "position" else name
        expected[target_name] = data[name]
    return expected


class IntentTracker:
    """Maintain a short queue of commands awaiting device confirmation."""

    def __init__(self, timeout: timedelta = CORRELATION_TIMEOUT) -> None:
        self.timeout = timeout
        self._pending: dict[str, deque[ServiceIntent]] = defaultdict(deque)

    def observe_call(
        self,
        event: Event,
        configured_entities: set[str],
    ) -> None:
        """Record relevant call_service events."""
        domain = event.data.get("domain")
        service = event.data.get("service")
        service_data = event.data.get("service_data") or {}
        if not isinstance(domain, str) or not isinstance(service, str):
            return
        if not isinstance(service_data, dict):
            return
        context: Context = event.context
        origin = classify_origin(context)
        expected = _expected_values(domain, service, service_data)
        for entity_id in _entity_ids(service_data.get(ATTR_ENTITY_ID)):
            if entity_id not in configured_entities:
                continue
            if entity_id.partition(".")[0] != domain:
                continue
            self._pending[entity_id].append(
                ServiceIntent(
                    entity_id=entity_id,
                    timestamp=event.time_fired,
                    service=f"{domain}.{service}",
                    expected=expected,
                    origin=origin,
                    context_id=context.id,
                    parent_id=context.parent_id,
                    user_id=context.user_id,
                )
            )
        self.prune(event.time_fired)

    def match(self, memory_event: MemoryEvent) -> ServiceIntent | None:
        """Return and consume the newest compatible pending intent."""
        self.prune(memory_event.timestamp)
        pending = self._pending.get(memory_event.entity_id)
        if not pending:
            return None
        for intent in reversed(pending):
            if self._matches(intent, memory_event):
                pending.remove(intent)
                if not pending:
                    self._pending.pop(memory_event.entity_id, None)
                return intent
        return None

    @staticmethod
    def _matches(intent: ServiceIntent, event: MemoryEvent) -> bool:
        if not intent.expected:
            return True
        for name, expected in intent.expected.items():
            actual = (
                event.new_state if name == "state" else event.new_attributes.get(name)
            )
            if actual != expected:
                return False
        return True

    def prune(self, now: datetime) -> None:
        """Remove commands that can no longer be correlated."""
        cutoff = now - self.timeout
        empty: list[str] = []
        for entity_id, intents in self._pending.items():
            while intents and intents[0].timestamp < cutoff:
                intents.popleft()
            if not intents:
                empty.append(entity_id)
        for entity_id in empty:
            self._pending.pop(entity_id, None)

    @property
    def pending_count(self) -> int:
        return sum(len(items) for items in self._pending.values())
