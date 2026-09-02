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
        _event("light.kitchen", now - timedelta(hours=2), "on", EventOrigin.AUTOMATION),
        now,
    )
    store.add(
        _event(
            "light.kitchen",
            now - timedelta(hours=1),
            "off",
            EventOrigin.AUTHENTICATED_COMMAND,
        ),
        now,
    )

    result = store.query(
        ["light.kitchen"],
        now - timedelta(hours=3),
        to_state="off",
        origins={EventOrigin.AUTHENTICATED_COMMAND},
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


def test_restore_merge_keeps_live_events_in_chronological_order() -> None:
    now = datetime(2026, 9, 1, 12, tzinfo=UTC)
    store = EventStore(timedelta(hours=12))
    store.add(
        _event("light.kitchen", now, "on", EventOrigin.AUTHENTICATED_COMMAND),
        now,
    )

    store.extend(
        [
            _event(
                "light.kitchen",
                now - timedelta(hours=1),
                "off",
                EventOrigin.UNKNOWN,
            )
        ],
        now,
    )

    result = store.query(["light.kitchen"], now - timedelta(hours=2))
    assert [event.new_state for event in result] == ["on", "off"]


def test_restore_merge_deduplicates_a_live_boundary_event() -> None:
    now = datetime(2026, 9, 1, 12, tzinfo=UTC)
    live = _event("light.kitchen", now, "on", EventOrigin.AUTHENTICATED_COMMAND)
    restored = _event("light.kitchen", now, "on", EventOrigin.UNKNOWN)
    store = EventStore(timedelta(hours=12))
    store.add(live, now)

    store.extend([restored], now)

    result = store.query(["light.kitchen"], now - timedelta(hours=1))
    assert result == [live]
