"""Tests for Recorder history normalization."""

from datetime import UTC, datetime, timedelta

from homeassistant.core import State

from custom_components.entity_memory.models import EventOrigin
from custom_components.entity_memory.recorder import _restored_events

START = datetime(2026, 9, 2, 6, tzinfo=UTC)


def _state(
    temperature: int,
    minutes: int,
    *,
    entity_id: str = "climate.living_room",
    state: str = "cool",
) -> State:
    timestamp = START + timedelta(minutes=minutes)
    return State(
        entity_id,
        state,
        {"temperature": temperature, "current_temperature": 27},
        last_changed=timestamp,
        last_reported=timestamp,
        last_updated=timestamp,
    )


def test_restores_significant_attribute_change_only() -> None:
    states = {
        "climate.living_room": [
            _state(24, -1),
            _state(24, 1),
            _state(23, 2),
        ]
    }

    events = _restored_events(
        states, START, include_attributes=True, ignore_unavailable=True
    )

    assert len(events) == 1
    assert events[0].changes["temperature"] == {"old": 24, "new": 23}
    assert events[0].origin is EventOrigin.UNKNOWN
    assert events[0].confidence == "low"
    assert events[0].context_id is None


def test_restored_binary_sensor_remains_unknown() -> None:
    states = {
        "binary_sensor.window": [
            _state(0, -1, entity_id="binary_sensor.window", state="off"),
            _state(0, 1, entity_id="binary_sensor.window", state="on"),
        ]
    }

    events = _restored_events(
        states, START, include_attributes=True, ignore_unavailable=True
    )

    assert len(events) == 1
    assert events[0].origin is EventOrigin.UNKNOWN
    assert events[0].confidence == "low"
    assert events[0].context_id is None


def test_ignores_unavailable_outage_and_recovery() -> None:
    states = {
        "climate.living_room": [
            _state(24, -1),
            _state(24, 1, state="unavailable"),
            _state(24, 2),
        ]
    }

    events = _restored_events(
        states, START, include_attributes=True, ignore_unavailable=True
    )

    assert events == []
