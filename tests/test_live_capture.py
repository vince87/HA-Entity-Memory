"""Tests for live transition selection before attribution and storage."""

from datetime import UTC, datetime

import pytest
from homeassistant.core import State

from custom_components.entity_memory import (
    _is_significant,
    _should_ignore_transition,
)

NOW = datetime(2026, 9, 5, 8, tzinfo=UTC)


def _state(
    entity_id: str,
    state: str,
    attributes: dict[str, object] | None = None,
) -> State:
    return State(
        entity_id,
        state,
        attributes or {},
        last_changed=NOW,
        last_reported=NOW,
        last_updated=NOW,
    )


@pytest.mark.parametrize(
    ("entity_id", "old", "new"),
    [
        ("light.example", "off", "on"),
        ("cover.example", "closed", "open"),
        ("climate.example", "off", "cool"),
        ("switch.example", "off", "on"),
        ("binary_sensor.example", "off", "on"),
    ],
)
def test_state_changes_are_significant_for_every_supported_domain(
    entity_id: str, old: str, new: str
) -> None:
    assert _is_significant(_state(entity_id, old), _state(entity_id, new), True)


@pytest.mark.parametrize(
    ("entity_id", "attribute", "old", "new"),
    [
        ("light.example", "brightness", 100, 150),
        ("cover.example", "current_position", 20, 70),
        ("climate.example", "temperature", 22, 23),
    ],
)
def test_domain_specific_attribute_changes_are_significant(
    entity_id: str, attribute: str, old: object, new: object
) -> None:
    assert _is_significant(
        _state(entity_id, "on", {attribute: old}),
        _state(entity_id, "on", {attribute: new}),
        True,
    )


def test_irrelevant_or_disabled_attribute_changes_are_ignored() -> None:
    old = _state("climate.example", "cool", {"current_temperature": 20})
    new = _state("climate.example", "cool", {"current_temperature": 21})
    assert not _is_significant(old, new, True)

    old = _state("light.example", "on", {"brightness": 100})
    new = _state("light.example", "on", {"brightness": 150})
    assert not _is_significant(old, new, False)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("on", "unknown"),
        ("unknown", "on"),
        ("on", "unavailable"),
        ("unavailable", "on"),
    ],
)
def test_ignored_state_outages_and_recoveries_are_symmetric(old: str, new: str) -> None:
    old_state = _state("switch.example", old)
    new_state = _state("switch.example", new)

    assert _should_ignore_transition(old_state, new_state, True)
    assert not _should_ignore_transition(old_state, new_state, False)
