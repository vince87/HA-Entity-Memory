"""Persistent, entity-less registers for automation state."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Protocol

MAX_REGISTER_VALUE_BYTES = 16_384
MAX_REGISTERS = 256


def _utcnow() -> datetime:
    return datetime.now(UTC)


class StorageBackend(Protocol):
    """Subset of Home Assistant Store used by the register store."""

    async def async_load(self) -> dict[str, Any] | None:
        """Load stored data."""

    async def async_save(self, data: dict[str, Any]) -> None:
        """Persist data."""


def validate_register_value(value: Any) -> Any:
    """Return a detached JSON value or raise ValueError."""
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
    except (TypeError, ValueError) as err:
        raise ValueError("Register values must be valid JSON") from err
    if len(encoded) > MAX_REGISTER_VALUE_BYTES:
        raise ValueError(
            f"Register value exceeds {MAX_REGISTER_VALUE_BYTES} encoded bytes"
        )
    return json.loads(encoded)


class RegisterStore:
    """Store small named values outside the Home Assistant entity registry."""

    def __init__(
        self,
        storage: StorageBackend,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._storage = storage
        self._now = now
        self._registers: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        """Restore registers from Home Assistant storage."""
        data = await self._storage.async_load()
        registers = data.get("registers", {}) if isinstance(data, dict) else {}
        if isinstance(registers, dict):
            self._registers = {
                key: record
                for key, record in registers.items()
                if isinstance(key, str)
                and isinstance(record, dict)
                and "value" in record
                and isinstance(record.get("revision"), int)
            }

    def get(self, key: str) -> dict[str, Any]:
        """Return one register in response-data form."""
        record = self._registers.get(key)
        if record is None:
            return {
                "found": False,
                "value": None,
                "revision": 0,
                "updated_at": None,
            }
        return {"found": True, **deepcopy(record)}

    async def async_set(
        self,
        key: str,
        value: Any,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        """Create or replace a register, optionally only at an expected revision."""
        value = validate_register_value(value)
        async with self._lock:
            previous = self._registers.get(key)
            current_revision = 0 if previous is None else previous["revision"]
            if expected_revision is not None and expected_revision != current_revision:
                return {
                    "created": False,
                    "changed": False,
                    "conflict": True,
                    "expected_revision": expected_revision,
                    **self.get(key),
                    "previous": None
                    if previous is None
                    else deepcopy(previous["value"]),
                }
            if previous is not None and previous["value"] == value:
                return {
                    "created": False,
                    "changed": False,
                    "conflict": False,
                    "previous": deepcopy(previous["value"]),
                    **self.get(key),
                }
            if previous is None and len(self._registers) >= MAX_REGISTERS:
                raise ValueError(f"Register limit of {MAX_REGISTERS} reached")
            record = {
                "value": value,
                "revision": 1 if previous is None else previous["revision"] + 1,
                "updated_at": self._now().isoformat(),
            }
            self._registers[key] = record
            await self._async_save()
            return {
                "created": previous is None,
                "changed": True,
                "conflict": False,
                "previous": None if previous is None else deepcopy(previous["value"]),
                "found": True,
                **deepcopy(record),
            }

    def compare(self, key: str, value: Any) -> dict[str, Any]:
        """Compare a value without changing the register."""
        value = validate_register_value(value)
        current = self.get(key)
        return {
            **current,
            "matches": current["found"] and current["value"] == value,
            "compared_value": value,
        }

    async def async_delete(self, key: str) -> dict[str, Any]:
        """Delete one register."""
        async with self._lock:
            previous = self._registers.pop(key, None)
            if previous is not None:
                await self._async_save()
            return {
                "deleted": previous is not None,
                "previous": None if previous is None else deepcopy(previous["value"]),
            }

    def list(self, prefix: str | None = None, limit: int = 100) -> dict[str, Any]:
        """Return registers ordered by key."""
        items = {
            key: deepcopy(self._registers[key])
            for key in sorted(self._registers)
            if prefix is None or key.startswith(prefix)
        }
        items = dict(list(items.items())[:limit])
        return {"registers": items, "count": len(items)}

    async def _async_save(self) -> None:
        await self._storage.async_save({"registers": deepcopy(self._registers)})
