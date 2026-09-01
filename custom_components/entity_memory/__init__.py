"""Entity Memory integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import Event, HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ATTRIBUTE_CHANGES,
    CONF_ENTITIES,
    CONF_IGNORE_UNAVAILABLE,
    CONF_WINDOW_HOURS,
    DEFAULT_ATTRIBUTE_CHANGES,
    DEFAULT_IGNORE_UNAVAILABLE,
    DEFAULT_WINDOW_HOURS,
    DOMAIN,
    IGNORED_STATES,
    SIGNIFICANT_ATTRIBUTES,
)
from .models import EventOrigin, MemoryEvent
from .store import EventStore

type EntityMemoryConfigEntry = ConfigEntry[EventStore]

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


async def async_setup_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> bool:
    """Set up Entity Memory from a config entry."""
    config = {**entry.data, **entry.options}
    entity_ids = list(config[CONF_ENTITIES])
    window = timedelta(
        hours=float(config.get(CONF_WINDOW_HOURS, DEFAULT_WINDOW_HOURS))
    )
    ignore_unavailable = config.get(
        CONF_IGNORE_UNAVAILABLE, DEFAULT_IGNORE_UNAVAILABLE
    )
    include_attributes = config.get(
        CONF_ATTRIBUTE_CHANGES, DEFAULT_ATTRIBUTE_CHANGES
    )
    store = EventStore(window)
    entry.runtime_data = store

    async def _state_changed(event: Event) -> None:
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        if ignore_unavailable and new_state.state in IGNORED_STATES:
            return
        if not _is_significant(old_state, new_state, include_attributes):
            return
        store.add(MemoryEvent.from_states(old_state, new_state), dt_util.utcnow())

    entry.async_on_unload(
        async_track_state_change_event(hass, entity_ids, _state_changed)
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    _register_actions(hass, entry)
    return True


def _register_actions(hass: HomeAssistant, entry: EntityMemoryConfigEntry) -> None:
    """Register query actions for the single config entry."""

    async def query(call: ServiceCall) -> dict[str, Any]:
        data = call.data
        since = dt_util.utcnow() - data["since"]
        origins = set(data["origins"]) if data.get("origins") else None
        events = entry.runtime_data.query(
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


async def _async_reload_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: EntityMemoryConfigEntry
) -> bool:
    """Unload Entity Memory."""
    for name in ("get_events", "last_event", "was_changed", "count_events"):
        hass.services.async_remove(DOMAIN, name)
    return True
