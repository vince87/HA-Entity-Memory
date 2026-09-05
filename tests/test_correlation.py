"""Tests for command-to-state correlation."""

from datetime import UTC, datetime, timedelta

from homeassistant.core import Context, Event

from custom_components.entity_memory.correlation import IntentTracker
from custom_components.entity_memory.models import (
    EventConfidence,
    EventOrigin,
    MemoryEvent,
    classify_origin,
)

ENTITY_ID = "climate.living_room"
NOW = datetime(2026, 9, 2, 16, 20, tzinfo=UTC)


def _call(*, temperature: int, context: Context, timestamp: datetime = NOW) -> Event:
    return Event(
        "call_service",
        {
            "domain": "climate",
            "service": "set_temperature",
            "service_data": {
                "entity_id": [ENTITY_ID],
                "temperature": temperature,
            },
        },
        time_fired_timestamp=timestamp.timestamp(),
        context=context,
    )


def _change(temperature: int, timestamp: datetime) -> MemoryEvent:
    return MemoryEvent(
        entity_id=ENTITY_ID,
        timestamp=timestamp,
        old_state="cool",
        new_state="cool",
        origin=EventOrigin.UNKNOWN,
        new_attributes={"temperature": temperature},
    )


def test_origin_vocabulary_and_context_classification_are_frozen() -> None:
    assert [origin.value for origin in EventOrigin] == [
        "automation",
        "authenticated_command",
        "external_or_physical",
        "device_observation",
        "unknown",
    ]
    assert [confidence.value for confidence in EventConfidence] == [
        "high",
        "medium",
        "low",
    ]
    assert classify_origin(Context(parent_id="parent")) is EventOrigin.AUTOMATION
    assert classify_origin(Context(user_id="user")) is EventOrigin.AUTHENTICATED_COMMAND
    assert classify_origin(Context()) is EventOrigin.UNKNOWN


def test_serialized_attribution_uses_public_string_values() -> None:
    event = _change(24, NOW).attributed(
        origin=EventOrigin.EXTERNAL_OR_PHYSICAL,
        confidence=EventConfidence.MEDIUM,
    )

    serialized = event.as_dict()

    assert serialized["origin"] == "external_or_physical"
    assert serialized["confidence"] == "medium"


def test_matches_automation_by_requested_value() -> None:
    tracker = IntentTracker()
    tracker.observe_call(
        _call(temperature=24, context=Context(parent_id="parent")), {ENTITY_ID}
    )

    intent = tracker.match(_change(24, NOW + timedelta(seconds=45)))

    assert intent is not None
    assert intent.origin is EventOrigin.AUTOMATION
    assert intent.service == "climate.set_temperature"


def test_recognizes_automation_by_exact_trigger_context() -> None:
    tracker = IntentTracker()
    context = Context()
    tracker.observe_automation(
        Event(
            "automation_triggered",
            {"entity_id": "automation.climate_control"},
            time_fired_timestamp=NOW.timestamp(),
            context=context,
        )
    )
    tracker.observe_call(
        _call(
            temperature=24,
            context=context,
            timestamp=NOW + timedelta(milliseconds=20),
        ),
        {ENTITY_ID},
    )

    intent = tracker.match(_change(24, NOW + timedelta(seconds=2)))

    assert intent is not None
    assert intent.origin is EventOrigin.AUTOMATION


def test_does_not_guess_automation_from_timing_alone() -> None:
    tracker = IntentTracker()
    tracker.observe_automation(
        Event(
            "automation_triggered",
            {"entity_id": "automation.other"},
            time_fired_timestamp=NOW.timestamp(),
            context=Context(),
        )
    )
    tracker.observe_call(
        _call(
            temperature=24,
            context=Context(),
            timestamp=NOW + timedelta(milliseconds=20),
        ),
        {ENTITY_ID},
    )

    intent = tracker.match(_change(24, NOW + timedelta(seconds=2)))

    assert intent is not None
    assert intent.origin is EventOrigin.UNKNOWN


def test_does_not_confuse_nearby_different_targets() -> None:
    tracker = IntentTracker()
    tracker.observe_call(
        _call(temperature=25, context=Context(user_id="user")), {ENTITY_ID}
    )
    tracker.observe_call(
        _call(
            temperature=24,
            context=Context(parent_id="parent"),
            timestamp=NOW + timedelta(seconds=44),
        ),
        {ENTITY_ID},
    )

    intent = tracker.match(_change(24, NOW + timedelta(seconds=60)))

    assert intent is not None
    assert intent.origin is EventOrigin.AUTOMATION


def test_expires_old_intents() -> None:
    tracker = IntentTracker(timeout=timedelta(seconds=180))
    tracker.observe_call(
        _call(temperature=24, context=Context(parent_id="parent")), {ENTITY_ID}
    )

    assert tracker.match(_change(24, NOW + timedelta(seconds=181))) is None


def test_ignores_query_action_targeting_a_configured_entity() -> None:
    tracker = IntentTracker()
    event = Event(
        "call_service",
        {
            "domain": "entity_memory",
            "service": "get_events",
            "service_data": {"entity_id": [ENTITY_ID]},
        },
        time_fired_timestamp=NOW.timestamp(),
        context=Context(user_id="user"),
    )

    tracker.observe_call(event, {ENTITY_ID})

    assert tracker.pending_count == 0
    assert tracker.match(_change(24, NOW + timedelta(seconds=10))) is None


def test_matches_climate_hvac_mode_against_entity_state() -> None:
    tracker = IntentTracker()
    event = Event(
        "call_service",
        {
            "domain": "climate",
            "service": "set_temperature",
            "service_data": {
                "entity_id": [ENTITY_ID],
                "hvac_mode": "cool",
                "temperature": 24,
            },
        },
        time_fired_timestamp=NOW.timestamp(),
        context=Context(parent_id="automation"),
    )

    tracker.observe_call(event, {ENTITY_ID})
    intent = tracker.match(_change(24, NOW + timedelta(seconds=2)))

    assert intent is not None
    assert intent.origin is EventOrigin.AUTOMATION
    assert intent.service == "climate.set_temperature"
