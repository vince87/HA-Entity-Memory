"""Tests for privacy-safe integration diagnostics."""

import json
from types import SimpleNamespace
from typing import Any

import pytest

from custom_components.entity_memory.const import REGISTER_STORAGE_VERSION
from custom_components.entity_memory.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.entity_memory.registers import (
    MAX_REGISTER_VALUE_BYTES,
    MAX_REGISTERS,
    RegisterStore,
)


class FakeStorage:
    """In-memory storage backend."""

    def __init__(self) -> None:
        self.data: dict[str, Any] | None = None

    async def async_load(self) -> dict[str, Any] | None:
        return self.data

    async def async_save(self, data: dict[str, Any]) -> None:
        self.data = data


@pytest.mark.asyncio
async def test_diagnostics_report_only_aggregate_register_data() -> None:
    registers = RegisterStore(FakeStorage())
    await registers.async_load()
    await registers.async_set("private.alarm_mode", "secret-value")
    await registers.async_set("private.schedule", {"person": "Vincenzo"})
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(
            entity_ids={"cover.private_shutter", "alarm_control_panel.private"},
            registers=registers,
        )
    )

    result = await async_get_config_entry_diagnostics(SimpleNamespace(), entry)

    assert result == {
        "tracked_entity_count": 2,
        "register_storage_version": REGISTER_STORAGE_VERSION,
        "registers": {
            "count": 2,
            "total_value_bytes": 35,
            "largest_value_bytes": 21,
            "maximum_count": MAX_REGISTERS,
            "maximum_value_bytes": MAX_REGISTER_VALUE_BYTES,
        },
    }
    serialized = json.dumps(result)
    for private_text in (
        "private.alarm_mode",
        "private.schedule",
        "secret-value",
        "Vincenzo",
        "cover.private_shutter",
        "alarm_control_panel.private",
    ):
        assert private_text not in serialized


@pytest.mark.asyncio
async def test_empty_register_diagnostics_have_zero_sizes() -> None:
    registers = RegisterStore(FakeStorage())
    await registers.async_load()

    assert registers.diagnostics() == {
        "count": 0,
        "total_value_bytes": 0,
        "largest_value_bytes": 0,
        "maximum_count": MAX_REGISTERS,
        "maximum_value_bytes": MAX_REGISTER_VALUE_BYTES,
    }
