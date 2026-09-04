"""Tests for persistent automation registers."""

from datetime import UTC, datetime
from typing import Any

import pytest

from custom_components.entity_memory.registers import (
    MAX_REGISTER_VALUE_BYTES,
    MAX_REGISTERS,
    RegisterStore,
    validate_register_value,
)


class FakeStorage:
    """Small in-memory replacement for Home Assistant Store."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        self.data = data
        self.save_count = 0

    async def async_load(self) -> dict[str, Any] | None:
        return self.data

    async def async_save(self, data: dict[str, Any]) -> None:
        self.data = data
        self.save_count += 1


@pytest.mark.asyncio
async def test_register_lifecycle_and_revision() -> None:
    storage = FakeStorage()
    now = datetime(2026, 9, 4, 12, tzinfo=UTC)
    registers = RegisterStore(storage, lambda: now)
    await registers.async_load()

    assert registers.get("shutters.west") == {
        "found": False,
        "value": None,
        "revision": 0,
        "updated_at": None,
    }

    created = await registers.async_set("shutters.west", "open")
    unchanged = await registers.async_set("shutters.west", "open")
    changed = await registers.async_set("shutters.west", {"mode": "shade"})

    assert created["created"] is True
    assert created["revision"] == 1
    assert unchanged["changed"] is False
    assert storage.save_count == 2
    assert changed["previous"] == "open"
    assert changed["revision"] == 2

    assert registers.compare("shutters.west", {"mode": "shade"})["matches"]
    assert not registers.compare("shutters.west", "open")["matches"]

    deleted = await registers.async_delete("shutters.west")
    assert deleted == {"deleted": True, "previous": {"mode": "shade"}}
    assert not registers.get("shutters.west")["found"]


@pytest.mark.asyncio
async def test_registers_restore_and_list_by_prefix() -> None:
    storage = FakeStorage(
        {
            "registers": {
                "lights.mode": {
                    "value": "night",
                    "revision": 2,
                    "updated_at": "2026-09-04T10:00:00+00:00",
                },
                "shutters.south": {
                    "value": True,
                    "revision": 3,
                    "updated_at": "2026-09-04T11:00:00+00:00",
                },
            }
        }
    )
    registers = RegisterStore(storage)
    await registers.async_load()

    result = registers.list("shutters.")
    assert result["count"] == 1
    assert result["registers"]["shutters.south"]["value"] is True


def test_register_values_must_be_bounded_json() -> None:
    assert validate_register_value([True, 4, "ok"]) == [True, 4, "ok"]

    with pytest.raises(ValueError, match="valid JSON"):
        validate_register_value({"bad": object()})
    with pytest.raises(ValueError, match="exceeds"):
        validate_register_value("x" * MAX_REGISTER_VALUE_BYTES)


@pytest.mark.asyncio
async def test_register_count_is_bounded() -> None:
    storage = FakeStorage()
    registers = RegisterStore(storage)
    await registers.async_load()
    for index in range(MAX_REGISTERS):
        await registers.async_set(f"test.{index}", index)

    with pytest.raises(ValueError, match="Register limit"):
        await registers.async_set("test.overflow", True)
