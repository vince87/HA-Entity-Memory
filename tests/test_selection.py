"""Tests for compact entity selection."""

from custom_components.entity_memory.selection import (
    known_entity_ids,
    parse_patterns,
    patterns_are_valid,
    resolve_entities,
)


def test_known_entity_ids_includes_registry_entities_not_loaded_as_states() -> None:
    assert known_entity_ids(
        ["light.loaded"], ["light.loaded", "light.registry_only"]
    ) == {"light.loaded", "light.registry_only"}


def test_parse_patterns_accepts_lines_and_commas() -> None:
    assert parse_patterns("light.*\nswitch.kitchen, cover.floor_*") == [
        "light.*",
        "switch.kitchen",
        "cover.floor_*",
    ]


def test_rejects_unsupported_or_malformed_patterns() -> None:
    assert patterns_are_valid(["light.*", "binary_sensor.window_?"])
    assert not patterns_are_valid(["sensor.*"])
    assert not patterns_are_valid(["light *"])


def test_resolve_entities_deduplicates_and_filters_domains() -> None:
    assert resolve_entities(
        ["light.sala_due"],
        ["light.*", "binary_sensor.*_window"],
        [
            "light.sala_uno",
            "light.sala_due",
            "binary_sensor.kitchen_window",
            "sensor.temperature",
        ],
    ) == {
        "light.sala_uno",
        "light.sala_due",
        "binary_sensor.kitchen_window",
    }


def test_resolve_entities_has_no_artificial_entity_limit() -> None:
    available = [f"light.test_{number}" for number in range(75)]

    assert len(resolve_entities([], ["light.*"], available)) == 75
