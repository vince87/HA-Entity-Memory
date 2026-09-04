"""Service-level contract tests for persistent registers."""

from datetime import timedelta
from types import SimpleNamespace
from typing import Any

import pytest
import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError

from custom_components.entity_memory import _register_actions
from custom_components.entity_memory.const import DOMAIN
from custom_components.entity_memory.registers import RegisterStore
from custom_components.entity_memory.store import EventStore


class FakeStorage:
    """In-memory storage backend."""

    def __init__(self) -> None:
        self.data: dict[str, Any] | None = None

    async def async_load(self) -> dict[str, Any] | None:
        return self.data

    async def async_save(self, data: dict[str, Any]) -> None:
        self.data = data


class FakeServices:
    """Apply registered HA schemas before invoking service handlers."""

    def __init__(self) -> None:
        self.registered: dict[str, tuple[Any, vol.Schema, SupportsResponse]] = {}

    def async_register(
        self,
        domain: str,
        name: str,
        handler: Any,
        *,
        schema: vol.Schema,
        supports_response: SupportsResponse,
    ) -> None:
        assert domain == DOMAIN
        self.registered[name] = (handler, schema, supports_response)

    async def call(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        handler, schema, supports_response = self.registered[name]
        assert supports_response is SupportsResponse.ONLY
        return await handler(SimpleNamespace(data=schema(data)))


class FakeConfigEntries:
    """Return the one loaded integration runtime."""

    def __init__(self, runtime: Any) -> None:
        self._entry = SimpleNamespace(runtime_data=runtime)

    def async_loaded_entries(self, domain: str) -> list[Any]:
        assert domain == DOMAIN
        return [self._entry]


async def _services() -> FakeServices:
    storage = FakeStorage()
    registers = RegisterStore(storage)
    await registers.async_load()
    services = FakeServices()
    hass = SimpleNamespace(
        services=services,
        config_entries=FakeConfigEntries(
            SimpleNamespace(
                registers=registers,
                store=EventStore(timedelta(hours=12)),
            )
        ),
    )
    _register_actions(hass)
    return services


@pytest.mark.asyncio
async def test_all_register_service_response_contracts() -> None:
    services = await _services()

    created = await services.call(
        "set_register",
        {"key": "test.phase", "value": {"mode": "day"}, "expected_revision": "0"},
    )
    assert created == {
        "created": True,
        "changed": True,
        "conflict": False,
        "previous": None,
        "found": True,
        "value": {"mode": "day"},
        "revision": 1,
        "updated_at": created["updated_at"],
    }

    assert await services.call("get_register", {"key": "test.phase"}) == {
        "found": True,
        "value": {"mode": "day"},
        "revision": 1,
        "updated_at": created["updated_at"],
    }
    compared = await services.call(
        "compare_register", {"key": "test.phase", "value": {"mode": "day"}}
    )
    assert compared["matches"] is True
    assert compared["compared_value"] == {"mode": "day"}

    listed = await services.call("list_registers", {"prefix": "test.", "limit": 10})
    assert listed == {
        "registers": {
            "test.phase": {
                "value": {"mode": "day"},
                "revision": 1,
                "updated_at": created["updated_at"],
            }
        },
        "count": 1,
    }

    assert await services.call("delete_register", {"key": "test.phase"}) == {
        "deleted": True,
        "previous": {"mode": "day"},
    }
    assert await services.call("get_register", {"key": "test.phase"}) == {
        "found": False,
        "value": None,
        "revision": 0,
        "updated_at": None,
    }


@pytest.mark.asyncio
async def test_set_service_returns_conflict_without_changing_value() -> None:
    services = await _services()
    await services.call(
        "set_register",
        {"key": "test.phase", "value": "first", "expected_revision": 0},
    )

    conflict = await services.call(
        "set_register",
        {"key": "test.phase", "value": "stale", "expected_revision": 0},
    )

    assert conflict["conflict"] is True
    assert conflict["changed"] is False
    assert conflict["value"] == "first"
    assert conflict["revision"] == 1
    assert (await services.call("get_register", {"key": "test.phase"}))["value"] == (
        "first"
    )


@pytest.mark.asyncio
async def test_service_schemas_reject_unsupported_or_invalid_data() -> None:
    services = await _services()

    with pytest.raises(vol.Invalid, match="extra keys not allowed"):
        await services.call(
            "compare_register",
            {"key": "test.phase", "value": "day", "expected_revision": 0},
        )
    with pytest.raises(vol.Invalid, match="non-negative integer"):
        await services.call(
            "set_register",
            {"key": "test.phase", "value": "day", "expected_revision": 1.5},
        )
    with pytest.raises(vol.Invalid):
        await services.call("get_register", {"key": "Invalid key"})


@pytest.mark.asyncio
async def test_service_translates_invalid_values_to_home_assistant_error() -> None:
    services = await _services()

    with pytest.raises(HomeAssistantError, match="valid JSON"):
        await services.call("set_register", {"key": "test.phase", "value": object()})
    with pytest.raises(HomeAssistantError, match="valid JSON"):
        await services.call(
            "compare_register", {"key": "test.phase", "value": object()}
        )


@pytest.mark.asyncio
async def test_missing_query_and_register_responses_are_consistent() -> None:
    services = await _services()
    query = {"entity_id": ["light.missing"], "since": "00:30:00"}

    assert await services.call("get_events", query) == {"events": [], "count": 0}
    assert await services.call("last_event", query) == {"event": None}
    assert await services.call("was_changed", query) == {
        "found": False,
        "event": None,
    }
    assert await services.call("count_events", query) == {"count": 0}
    assert await services.call("get_register", {"key": "test.missing"}) == {
        "found": False,
        "value": None,
        "revision": 0,
        "updated_at": None,
    }
    assert await services.call(
        "compare_register", {"key": "test.missing", "value": None}
    ) == {
        "found": False,
        "value": None,
        "revision": 0,
        "updated_at": None,
        "matches": False,
        "compared_value": None,
    }
