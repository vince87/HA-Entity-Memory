"""Privacy-safe diagnostics for Entity Memory."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import EntityMemoryConfigEntry
from .const import REGISTER_STORAGE_VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: EntityMemoryConfigEntry,
) -> dict[str, Any]:
    """Return aggregate runtime data without entity IDs, keys, or values."""
    runtime = entry.runtime_data
    return {
        "tracked_entity_count": len(runtime.entity_ids),
        "register_storage_version": REGISTER_STORAGE_VERSION,
        "registers": runtime.registers.diagnostics(),
    }
