"""Data models for Entity Memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from homeassistant.core import Context, State

from .const import SIGNIFICANT_ATTRIBUTES


class EventOrigin(StrEnum):
    """Best-effort origin classification."""

    AUTOMATION = "automation"
    AUTHENTICATED_COMMAND = "authenticated_command"
    EXTERNAL_OR_PHYSICAL = "external_or_physical"
    DEVICE_OBSERVATION = "device_observation"
    UNKNOWN = "unknown"


def classify_origin(context: Context) -> EventOrigin:
    """Classify an event from Home Assistant context metadata."""
    if context.parent_id:
        return EventOrigin.AUTOMATION
    if context.user_id:
        return EventOrigin.AUTHENTICATED_COMMAND
    return EventOrigin.UNKNOWN


def relevant_attributes(state: State) -> dict[str, Any]:
    """Return only attributes meaningful for the entity domain."""
    domain = state.entity_id.partition(".")[0]
    names = SIGNIFICANT_ATTRIBUTES.get(domain, frozenset())
    return {name: state.attributes[name] for name in names if name in state.attributes}


@dataclass(slots=True, frozen=True)
class MemoryEvent:
    """A normalized state transition retained by Entity Memory."""

    entity_id: str
    timestamp: datetime
    old_state: str | None
    new_state: str
    origin: EventOrigin
    context_id: str | None = None
    parent_id: str | None = None
    user_id: str | None = None
    old_attributes: dict[str, Any] = field(default_factory=dict)
    new_attributes: dict[str, Any] = field(default_factory=dict)
    changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    confidence: str = "low"
    matched_service: str | None = None

    @classmethod
    def from_states(cls, old_state: State | None, new_state: State) -> MemoryEvent:
        """Create an event from Home Assistant states."""
        context = new_state.context
        old_attributes = relevant_attributes(old_state) if old_state else {}
        new_attributes = relevant_attributes(new_state)
        changes: dict[str, dict[str, Any]] = {}
        if old_state is None or old_state.state != new_state.state:
            changes["state"] = {
                "old": old_state.state if old_state else None,
                "new": new_state.state,
            }
        for name in old_attributes.keys() | new_attributes.keys():
            if old_attributes.get(name) != new_attributes.get(name):
                changes[name] = {
                    "old": old_attributes.get(name),
                    "new": new_attributes.get(name),
                }
        origin = classify_origin(context)
        return cls(
            entity_id=new_state.entity_id,
            timestamp=new_state.last_updated,
            old_state=old_state.state if old_state else None,
            new_state=new_state.state,
            origin=origin,
            context_id=context.id,
            parent_id=context.parent_id,
            user_id=context.user_id,
            old_attributes=old_attributes,
            new_attributes=new_attributes,
            changes=changes,
            confidence="high" if origin is not EventOrigin.UNKNOWN else "low",
        )

    def attributed(
        self,
        *,
        origin: EventOrigin,
        confidence: str,
        context_id: str | None = None,
        parent_id: str | None = None,
        user_id: str | None = None,
        matched_service: str | None = None,
    ) -> MemoryEvent:
        """Return a copy carrying correlated attribution."""
        return replace(
            self,
            origin=origin,
            confidence=confidence,
            context_id=context_id or self.context_id,
            parent_id=parent_id,
            user_id=user_id,
            matched_service=matched_service,
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a service-response-safe representation."""
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        value["origin"] = self.origin.value
        return value
