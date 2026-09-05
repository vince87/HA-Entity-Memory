"""Entity Memory integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import voluptuous as vol
from homeassistant.components.automation import EVENT_AUTOMATION_TRIGGERED
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, EVENT_CALL_SERVICE
from homeassistant.core import (
    Event,
    HomeAssistant,
    ServiceCall,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ATTRIBUTE_CHANGES,
    CONF_ENTITIES,
    CONF_ENTITY_PATTERNS,
    CONF_IGNORE_UNAVAILABLE,
    CONF_WINDOW_HOURS,
    DEFAULT_ATTRIBUTE_CHANGES,
    DEFAULT_IGNORE_UNAVAILABLE,
    DEFAULT_WINDOW_HOURS,
    DOMAIN,
    IGNORED_STATES,
    REGISTER_STORAGE_KEY,
    REGISTER_STORAGE_VERSION,
    SIGNIFICANT_ATTRIBUTES,
)
from .correlation import IntentTracker
from .models import EventConfidence, EventOrigin, MemoryEvent
from .recorder import async_restore_events
from .registers import RegisterStore
from .selection import known_entity_ids, parse_patterns, resolve_entities
from .store import EventStore

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass(slots=True)
class EntityMemoryRuntime:
    """Runtime state for the single config entry."""

    store: EventStore
    intents: IntentTracker
    entity_ids: set[str]
    registers: RegisterStore


type EntityMemoryConfigEntry = ConfigEntry[EntityMemoryRuntime]


def _available_entity_ids(hass: HomeAssistant) -> set[str]:
    """Return entities known from both the state machine and registry."""
    return known_entity_ids(hass.states.async_entity_ids(), er.async_get(hass).entities)


QUERY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional("since", default="12:00:00"): cv.time_period,
        vol.Optional("to_state"): cv.string,
        vol.Optional("origins"): vol.All(cv.ensure_list, [vol.Coerce(EventOrigin)]),
        vol.Optional("limit", default=100): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1000)
        ),
    }
)

REGISTER_KEY = vol.All(
    cv.string,
    vol.Length(min=1, max=128),
    vol.Match(r"^[a-z0-9][a-z0-9_.-]*$"),
)
REGISTER_KEY_SCHEMA = vol.Schema({vol.Required("key"): REGISTER_KEY})


def _non_negative_revision(value: Any) -> int:
    """Validate an integer revision without lossy numeric coercion."""
    if isinstance(value, bool):
        raise vol.Invalid("expected_revision must be a non-negative integer")
    if isinstance(value, int):
        if value >= 0:
            return value
        raise vol.Invalid("expected_revision must be a non-negative integer")
    if isinstance(value, str) and value.isascii() and value.isdigit():
        try:
            return int(value)
        except ValueError as err:
            raise vol.Invalid(
                "expected_revision must be a non-negative integer"
            ) from err
    raise vol.Invalid("expected_revision must be a non-negative integer")


REGISTER_SET_SCHEMA = vol.Schema(
    {
        vol.Required("key"): REGISTER_KEY,
        vol.Required("value"): object,
        vol.Optional("expected_revision"): _non_negative_revision,
    }
)
REGISTER_COMPARE_SCHEMA = vol.Schema(
    {vol.Required("key"): REGISTER_KEY, vol.Required("value"): object}
)
REGISTER_LIST_SCHEMA = vol.Schema(
    {
        vol.Optional("prefix"): vol.All(cv.string, vol.Length(max=128)),
        vol.Optional("limit", default=100): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1000)
        ),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration-level actions."""
    _register_actions(hass)
    return True


def _is_significant(old_state, new_state, include_attributes: bool) -> bool:
    """Return whether a transition should be retained."""
    if old_state is None or old_state.state != new_state.state:
        return True
    if not include_attributes:
        return False
    domain = new_state.entity_id.partition(".")[0]
    return any(
        old_state.attributes.get(name) != new_state.attributes.get(name)
        for name in SIGNIFICANT_ATTRIBUTES.get(domain, ())
    )


def _should_ignore_transition(old_state, new_state, ignore_unavailable: bool) -> bool:
    """Return whether an unavailable/unknown boundary must be skipped."""
    return ignore_unavailable and (
        new_state.state in IGNORED_STATES or old_state.state in IGNORED_STATES
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> bool:
    """Set up Entity Memory from a config entry."""
    config = {**entry.data, **entry.options}
    patterns = parse_patterns(config.get(CONF_ENTITY_PATTERNS))
    entity_ids = resolve_entities(
        config.get(CONF_ENTITIES, []),
        patterns,
        _available_entity_ids(hass),
    )
    window = timedelta(hours=float(config.get(CONF_WINDOW_HOURS, DEFAULT_WINDOW_HOURS)))
    ignore_unavailable = config.get(CONF_IGNORE_UNAVAILABLE, DEFAULT_IGNORE_UNAVAILABLE)
    include_attributes = config.get(CONF_ATTRIBUTE_CHANGES, DEFAULT_ATTRIBUTE_CHANGES)
    store = EventStore(window)
    intents = IntentTracker()
    registers = RegisterStore(
        Store(hass, REGISTER_STORAGE_VERSION, REGISTER_STORAGE_KEY)
    )
    await registers.async_load()
    entry.runtime_data = EntityMemoryRuntime(store, intents, entity_ids, registers)

    async def _service_called(event: Event) -> None:
        intents.observe_call(event, entity_ids)

    async def _automation_triggered(event: Event) -> None:
        intents.observe_automation(event)

    async def _state_changed(event: Event) -> None:
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if old_state is None or new_state is None:
            return
        if _should_ignore_transition(old_state, new_state, ignore_unavailable):
            return
        if not _is_significant(old_state, new_state, include_attributes):
            return
        memory_event = MemoryEvent.from_states(old_state, new_state)
        if intent := intents.match(memory_event):
            memory_event = memory_event.attributed(
                origin=intent.origin,
                confidence=EventConfidence.HIGH,
                context_id=intent.context_id,
                parent_id=intent.parent_id,
                user_id=intent.user_id,
                matched_service=intent.service,
            )
        elif memory_event.origin is EventOrigin.UNKNOWN:
            domain = memory_event.entity_id.partition(".")[0]
            memory_event = memory_event.attributed(
                origin=(
                    EventOrigin.DEVICE_OBSERVATION
                    if domain == "binary_sensor"
                    else EventOrigin.EXTERNAL_OR_PHYSICAL
                ),
                confidence=(
                    EventConfidence.HIGH
                    if domain == "binary_sensor"
                    else EventConfidence.MEDIUM
                ),
            )
        store.add(memory_event, dt_util.utcnow())

    entry.async_on_unload(
        async_track_state_change_event(hass, list(entity_ids), _state_changed)
    )
    entry.async_on_unload(hass.bus.async_listen(EVENT_CALL_SERVICE, _service_called))
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_AUTOMATION_TRIGGERED, _automation_triggered)
    )

    if patterns:
        reload_pending = False

        async def _reload_after_registry_update(_now) -> None:
            nonlocal reload_pending
            reload_pending = False
            await hass.config_entries.async_reload(entry.entry_id)

        @callback
        def _entity_registry_updated(
            _event: Event[er.EventEntityRegistryUpdatedData],
        ) -> None:
            """Reload when a registry change alters wildcard expansion."""
            nonlocal reload_pending
            resolved = resolve_entities(
                config.get(CONF_ENTITIES, []),
                patterns,
                _available_entity_ids(hass),
            )
            if reload_pending or resolved == entity_ids:
                return
            reload_pending = True
            entry.async_on_unload(
                async_call_later(hass, 1, _reload_after_registry_update)
            )

        entry.async_on_unload(
            hass.bus.async_listen(
                er.EVENT_ENTITY_REGISTRY_UPDATED, _entity_registry_updated
            )
        )

    now = dt_util.utcnow()
    restored = await async_restore_events(
        hass,
        entity_ids,
        now - window,
        now,
        include_attributes=include_attributes,
        ignore_unavailable=ignore_unavailable,
    )
    store.extend(restored, dt_util.utcnow())

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


def _register_actions(hass: HomeAssistant) -> None:
    """Register query actions independently of config-entry state."""

    def _runtime() -> EntityMemoryRuntime:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("Entity Memory is not configured or loaded")
        return entries[0].runtime_data

    async def query(call: ServiceCall) -> dict[str, Any]:
        data = call.data
        since = dt_util.utcnow() - data["since"]
        origins = set(data["origins"]) if data.get("origins") else None
        events = _runtime().store.query(
            data[ATTR_ENTITY_ID],
            since,
            to_state=data.get("to_state"),
            origins=origins,
        )[: data["limit"]]
        return {
            "events": [event.as_dict() for event in events],
            "count": len(events),
        }

    async def last_event(call: ServiceCall) -> dict[str, Any]:
        response = await query(call)
        return {"event": response["events"][0] if response["events"] else None}

    async def was_changed(call: ServiceCall) -> dict[str, Any]:
        response = await query(call)
        return {
            "found": bool(response["count"]),
            "event": response["events"][0] if response["events"] else None,
        }

    async def count_events(call: ServiceCall) -> dict[str, Any]:
        response = await query(call)
        return {"count": response["count"]}

    async def get_register(call: ServiceCall) -> dict[str, Any]:
        return _runtime().registers.get(call.data["key"])

    async def set_register(call: ServiceCall) -> dict[str, Any]:
        try:
            return await _runtime().registers.async_set(
                call.data["key"],
                call.data["value"],
                call.data.get("expected_revision"),
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    async def compare_register(call: ServiceCall) -> dict[str, Any]:
        try:
            return _runtime().registers.compare(call.data["key"], call.data["value"])
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    async def delete_register(call: ServiceCall) -> dict[str, Any]:
        return await _runtime().registers.async_delete(call.data["key"])

    async def list_registers(call: ServiceCall) -> dict[str, Any]:
        return _runtime().registers.list(call.data.get("prefix"), call.data["limit"])

    for name, handler in {
        "get_events": query,
        "last_event": last_event,
        "was_changed": was_changed,
        "count_events": count_events,
    }.items():
        hass.services.async_register(
            DOMAIN,
            name,
            handler,
            schema=QUERY_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    for name, handler, schema in (
        ("get_register", get_register, REGISTER_KEY_SCHEMA),
        ("set_register", set_register, REGISTER_SET_SCHEMA),
        ("compare_register", compare_register, REGISTER_COMPARE_SCHEMA),
        ("delete_register", delete_register, REGISTER_KEY_SCHEMA),
        ("list_registers", list_registers, REGISTER_LIST_SCHEMA),
    ):
        hass.services.async_register(
            DOMAIN,
            name,
            handler,
            schema=schema,
            supports_response=SupportsResponse.ONLY,
        )


async def _async_reload_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> bool:
    """Unload Entity Memory."""
    return True
