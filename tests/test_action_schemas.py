"""Tests for public action validation schemas."""

import pytest
import voluptuous as vol

from custom_components.entity_memory import (
    REGISTER_COMPARE_SCHEMA,
    REGISTER_SET_SCHEMA,
)


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [(0, 0), (1, 1), (42, 42), ("0", 0), ("1", 1), ("42", 42)],
)
def test_set_register_accepts_non_negative_integer_revisions(
    supplied: object, expected: int
) -> None:
    validated = REGISTER_SET_SCHEMA(
        {"key": "example.phase", "value": "active", "expected_revision": supplied}
    )

    assert validated["expected_revision"] == expected


@pytest.mark.parametrize(
    "supplied",
    [
        True,
        False,
        -1,
        1.0,
        1.9,
        "-1",
        "+1",
        "1.0",
        "1.9",
        " 1",
        "1 ",
        "one",
        "",
    ],
)
def test_set_register_rejects_invalid_revisions(supplied: object) -> None:
    with pytest.raises(vol.Invalid, match="non-negative integer"):
        REGISTER_SET_SCHEMA(
            {
                "key": "example.phase",
                "value": "active",
                "expected_revision": supplied,
            }
        )


def test_compare_register_rejects_expected_revision() -> None:
    with pytest.raises(vol.Invalid, match="extra keys not allowed"):
        REGISTER_COMPARE_SCHEMA(
            {
                "key": "example.phase",
                "value": "active",
                "expected_revision": 1,
            }
        )


def test_compare_register_accepts_only_key_and_value() -> None:
    assert REGISTER_COMPARE_SCHEMA(
        {"key": "example.phase", "value": {"mode": "active"}}
    ) == {"key": "example.phase", "value": {"mode": "active"}}
