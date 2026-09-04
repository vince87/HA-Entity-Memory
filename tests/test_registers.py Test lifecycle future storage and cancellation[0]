"""Tests for persistent automation registers."""

import asyncio
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


class FailingStorage(FakeStorage):
    """Storage backend that rejects every save."""

    async def async_save(self, data: dict[str, Any]) -> None:
        raise RuntimeError("storage unavailable")


class FutureVersionStorage(FakeStorage):
    """Model Home Assistant refusing storage from a newer version."""

    async def async_load(self) -> dict[str, Any] | None:
        raise RuntimeError("unsupported future storage version")


class ControlledStorage(FakeStorage):
    """Pause a save so cancellation behavior can be exercised."""

    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.finish = asyncio.Event()

    async def async_save(self, data: dict[str, Any]) -> None:
        self.started.set()
        await self.finish.wait()
        await super().async_save(data)


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


@pytest.mark.asyncio
async def test_expected_revision_prevents_lost_updates() -> None:
    storage = FakeStorage()
    registers = RegisterStore(storage)
    await registers.async_load()

    missing_conflict = await registers.async_set(
        "automation.phase", "first", expected_revision=1
    )
    assert missing_conflict["conflict"] is True
    assert missing_conflict["revision"] == 0
    assert storage.save_count == 0

    created = await registers.async_set(
        "automation.phase", "first", expected_revision=0
    )
    assert created["conflict"] is False
    assert created["revision"] == 1

    stale = await registers.async_set("automation.phase", "stale", expected_revision=0)
    assert stale["conflict"] is True
    assert stale["value"] == "first"
    assert stale["revision"] == 1
    assert storage.save_count == 1

    updated = await registers.async_set(
        "automation.phase", "second", expected_revision=1
    )
    assert updated["conflict"] is False
    assert updated["value"] == "second"
    assert updated["revision"] == 2


@pytest.mark.asyncio
async def test_simultaneous_writers_allow_exactly_one_revision() -> None:
    storage = FakeStorage()
    registers = RegisterStore(storage)
    await registers.async_load()

    first, second = await asyncio.gather(
        registers.async_set("automation.phase", "first", expected_revision=0),
        registers.async_set("automation.phase", "second", expected_revision=0),
    )

    assert sorted(result["conflict"] for result in (first, second)) == [False, True]
    winner = first if not first["conflict"] else second
    assert registers.get("automation.phase")["value"] == winner["value"]
    assert registers.get("automation.phase")["revision"] == 1
    assert storage.save_count == 1


@pytest.mark.asyncio
async def test_failed_save_preserves_last_committed_value() -> None:
    initial = {
        "registers": {
            "automation.phase": {
                "value": "committed",
                "revision": 4,
                "updated_at": "2026-09-04T10:00:00+00:00",
            }
        }
    }
    registers = RegisterStore(FailingStorage(initial))
    await registers.async_load()

    with pytest.raises(RuntimeError, match="storage unavailable"):
        await registers.async_set("automation.phase", "uncommitted")
    assert registers.get("automation.phase")["value"] == "committed"
    assert registers.get("automation.phase")["revision"] == 4

    with pytest.raises(RuntimeError, match="storage unavailable"):
        await registers.async_delete("automation.phase")
    assert registers.get("automation.phase")["value"] == "committed"


@pytest.mark.asyncio
async def test_load_keeps_valid_records_and_ignores_malformed_records() -> None:
    valid = {
        "value": {"mode": "night"},
        "revision": 2,
        "updated_at": "2026-09-04T10:00:00+00:00",
    }
    storage = FakeStorage(
        {
            "registers": {
                "valid.phase": valid,
                "Bad Key": valid,
                "bad.boolean_revision": {**valid, "revision": True},
                "bad.negative_revision": {**valid, "revision": -1},
                "bad.timestamp": {**valid, "updated_at": "not-a-date"},
                "bad.missing_value": {
                    "revision": 1,
                    "updated_at": "2026-09-04T10:00:00+00:00",
                },
            }
        }
    )
    registers = RegisterStore(storage)

    await registers.async_load()

    assert registers.list() == {
        "registers": {"valid.phase": valid},
        "count": 1,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("stored", [None, [], "invalid", {"registers": []}])
async def test_load_treats_missing_or_invalid_root_as_empty(stored: Any) -> None:
    registers = RegisterStore(FakeStorage(stored))
    await registers.async_load()

    assert registers.list() == {"registers": {}, "count": 0}


@pytest.mark.asyncio
async def test_new_store_instance_restores_existing_registers() -> None:
    """Config-entry removal and re-add must not erase register storage."""
    storage = FakeStorage()
    before_removal = RegisterStore(storage)
    await before_removal.async_load()
    created = await before_removal.async_set("automation.phase", "active")

    after_readd = RegisterStore(storage)
    await after_readd.async_load()

    assert after_readd.get("automation.phase") == {
        "found": True,
        "value": "active",
        "revision": 1,
        "updated_at": created["updated_at"],
    }


@pytest.mark.asyncio
async def test_future_storage_rejection_fails_closed_without_overwrite() -> None:
    storage = FutureVersionStorage({"registers": {"future.private": {}}})
    registers = RegisterStore(storage)

    with pytest.raises(RuntimeError, match="future storage version"):
        await registers.async_load()

    assert storage.save_count == 0
    assert registers.list() == {"registers": {}, "count": 0}


@pytest.mark.asyncio
async def test_cancellation_waits_for_accepted_save_to_commit() -> None:
    storage = ControlledStorage()
    registers = RegisterStore(storage)
    await registers.async_load()
    writer = asyncio.create_task(registers.async_set("automation.phase", "committed"))
    await storage.started.wait()

    writer.cancel()
    storage.finish.set()

    with pytest.raises(asyncio.CancelledError):
        await writer
    assert storage.save_count == 1
    assert storage.data is not None
    assert storage.data["registers"]["automation.phase"]["value"] == "committed"
    assert registers.get("automation.phase")["value"] == "committed"


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
