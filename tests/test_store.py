"""Tests for the event store."""

from datetime import UTC, datetime, timedelta

from custom_components.entity_memory.models import EventOrigin, MemoryEvent
from custom_components.entity_memory.store import EventStore


def _event(
    entity_id: str, timestamp: datetime, state: str, origin: EventOrigin
) -> MemoryEvent:
    return MemoryEvent(entity_id, timestamp, None, state, origin)


def test_query_filters_and_orders() -> None:
    now = datetime(2026, 9, 1, 12, tzinfo=UTC)
    store = EventStore(timedelta(hours=12))
    store.add(
        _event(
            "light.kitchen", now - timedelta(hours=2), "on", EventOrigin.AUTOMATION
        ),
        now,
    )
    store.add(
        _event("light.kitchen", now - timedelta(hours=1), "off", EventOrigin.USER),
        now,
    )

    result = store.query(
        ["light.kitchen"],
        now - timedelta(hours=3),
        to_state="off",
        origins={EventOrigin.USER},
    )

    assert len(result) == 1
    assert result[0].new_state == "off"


def test_prunes_expired_events() -> None:
    now = datetime(2026, 9, 1, 12, tzinfo=UTC)
    store = EventStore(timedelta(hours=12))
    store.add(
        _event(
            "binary_sensor.door",
            now - timedelta(hours=13),
            "on",
            EventOrigin.UNKNOWN,
        ),
        now,
    )
    assert store.event_count == 0
