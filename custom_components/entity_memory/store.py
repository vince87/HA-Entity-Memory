"""Bounded in-memory event store."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from datetime import datetime, timedelta
from heapq import nlargest

from .models import EventOrigin, MemoryEvent
from .packed import PackedEvent


class EventStore:
    """Keep a rolling event window without duplicating Recorder persistence."""

    def __init__(self, window: timedelta) -> None:
        self.window = window
        self._events: dict[str, deque[PackedEvent]] = defaultdict(deque)
        self._next_prune: datetime | None = None

    def add(self, event: MemoryEvent, now: datetime | None = None) -> None:
        """Add an event and evict expired entries."""
        self._events[event.entity_id].append(PackedEvent.pack(event))
        now = now or event.timestamp
        events = self._events[event.entity_id]
        while events and events[0].timestamp < now - self.window:
            events.popleft()
        if self._next_prune is None or now >= self._next_prune:
            self.prune(now)
            self._next_prune = now + timedelta(minutes=1)

    def extend(self, events: Iterable[MemoryEvent], now: datetime) -> None:
        """Merge restored and live events in chronological order."""
        touched: set[str] = set()
        events = list(events)
        restoring = {event.entity_id for event in events}
        existing = {
            (entity_id, event.timestamp, event.old_state, event.new_state)
            for entity_id, entity_events in self._events.items()
            if entity_id in restoring
            for event in entity_events
        }
        for event in events:
            identity = (
                event.entity_id,
                event.timestamp,
                event.old_state,
                event.new_state,
            )
            if identity in existing:
                continue
            self._events[event.entity_id].append(PackedEvent.pack(event))
            touched.add(event.entity_id)
            existing.add(identity)
        for entity_id in touched:
            self._events[entity_id] = deque(
                sorted(self._events[entity_id], key=lambda item: item.timestamp)
            )
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
        limit: int | None = None,
    ) -> list[MemoryEvent]:
        """Query matching events, newest first."""
        result = (
            event
            for entity_id in entity_ids
            for event in self._events.get(entity_id, ())
            if event.timestamp >= since
            and (to_state is None or event.new_state == to_state)
            and (origins is None or event.origin in origins)
        )
        ordered = (
            nlargest(limit, result, key=lambda item: item.timestamp)
            if limit is not None
            else sorted(result, key=lambda item: item.timestamp, reverse=True)
        )
        return [event.unpack() for event in ordered]

    @property
    def event_count(self) -> int:
        """Return the number of cached events."""
        return sum(len(events) for events in self._events.values())
