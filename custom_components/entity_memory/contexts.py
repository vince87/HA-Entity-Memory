"""Bounded native context ancestry, independent of service targets."""

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.core import Event

from .models import EventConfidence, EventOrigin, MemoryEvent


@dataclass(frozen=True, slots=True)
class Cause:
    timestamp: datetime
    parent_id: str | None
    user_id: str | None
    automation: bool
    service: str | None


class ContextCache:
    """Resolve exact relationships before falling back to legacy attribution."""

    def __init__(self, capacity: int = 4096) -> None:
        self.capacity = capacity
        self._causes: OrderedDict[str, Cause] = OrderedDict()

    def observe(self, event: Event) -> None:
        context = event.context
        previous = self._causes.get(context.id)
        service = None
        if event.event_type == "call_service":
            service = f"{event.data.get('domain')}.{event.data.get('service')}"
        self._causes[context.id] = Cause(
            event.time_fired,
            context.parent_id,
            context.user_id or (previous.user_id if previous else None),
            event.event_type in {"automation_triggered", "script_started"}
            or bool(previous and previous.automation),
            service or (previous.service if previous else None),
        )
        self._causes.move_to_end(context.id)
        while len(self._causes) > self.capacity:
            self._causes.popitem(last=False)

    def resolve(self, event: MemoryEvent) -> MemoryEvent | None:
        context_id = event.context_id
        visited: set[str] = set()
        user_id = event.user_id
        service = None
        automation = False
        evidence = bool(user_id)
        for _ in range(32):
            if not context_id or context_id in visited:
                break
            visited.add(context_id)
            cause = self._causes.get(context_id)
            if cause is None:
                if context_id == event.context_id:
                    context_id = event.parent_id
                    continue
                break
            if (
                not timedelta(0)
                <= event.timestamp - cause.timestamp
                <= timedelta(hours=1)
            ):
                break
            evidence = True
            automation |= cause.automation
            user_id = user_id or cause.user_id
            service = service or cause.service
            context_id = cause.parent_id
        if not evidence:
            return None
        origin = (
            EventOrigin.AUTOMATION
            if automation
            else EventOrigin.AUTHENTICATED_COMMAND
            if user_id
            else EventOrigin.UNKNOWN
        )
        return event.attributed(
            origin=origin,
            confidence=EventConfidence.HIGH
            if origin != EventOrigin.UNKNOWN
            else EventConfidence.LOW,
            context_id=event.context_id,
            parent_id=event.parent_id,
            user_id=user_id,
            matched_service=service,
        )
