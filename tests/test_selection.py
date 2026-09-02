"""Tests for compact entity selection."""

from custom_components.entity_memory.selection import (
    parse_patterns,
    patterns_are_valid,
    resolve_entities,
)


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
