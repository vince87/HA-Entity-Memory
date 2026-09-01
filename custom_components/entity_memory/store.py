"""Bounded in-memory event store."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import EventOrigin, MemoryEvent


class EventStore:
    """Keep a rolling event window without duplicating Recorder persistence."""

    def __init__(self, window: timedelta) -> None:
        self.window = window
        self._events: dict[str, deque[MemoryEvent]] = defaultdict(deque)

    def add(self, event: MemoryEvent, now: datetime | None = None) -> None:
        """Add an event and evict expired entries."""
        self._events[event.entity_id].append(event)
        self.prune(now or event.timestamp)

    def extend(self, events: Iterable[MemoryEvent], now: datetime) -> None:
        """Add restored events in chronological order."""
        for event in sorted(events, key=lambda item: item.timestamp):
            self._events[event.entity_id].append(event)
        self.prune(now)

    def prune(self, now: datetime) -> None:
        """Remove events outside the rolling window."""
        cutoff = now - self.window
        empty: list[str] = []
        for entity_id, events in self._events.items():
            while events and events[0].timestamp < cutoff:
                events.popleft()
            if not events:
                empty.append(entity_id)
        for entity_id in empty:
            self._events.pop(entity_id, None)

    def query(
        self,
        entity_ids: Iterable[str],
        since: datetime,
        *,
        to_state: str | None = None,
        origins: set[EventOrigin] | None = None,
    ) -> list[MemoryEvent]:
        """Query matching events, newest first."""
        result = [
            event
            for entity_id in entity_ids
            for event in self._events.get(entity_id, ())
            if event.timestamp >= since
            and (to_state is None or event.new_state == to_state)
            and (origins is None or event.origin in origins)
        ]
        return sorted(result, key=lambda item: item.timestamp, reverse=True)

    @property
    def event_count(self) -> int:
        """Return the number of cached events."""
        return sum(len(events) for events in self._events.values())
