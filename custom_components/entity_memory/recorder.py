"""Restore Entity Memory's rolling cache from Home Assistant Recorder."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime

from homeassistant.components.recorder import get_instance, history
from homeassistant.core import HomeAssistant, State

from .const import IGNORED_STATES, SIGNIFICANT_ATTRIBUTES
from .models import EventOrigin, MemoryEvent


def _restored_events(
    states_by_entity: Mapping[str, Sequence[State]],
    start: datetime,
    *,
    include_attributes: bool,
    ignore_unavailable: bool,
) -> list[MemoryEvent]:
    """Convert Recorder state rows into normalized transitions."""
    restored: list[MemoryEvent] = []
    for states in states_by_entity.values():
        old_state: State | None = None
        for new_state in states:
            if new_state.last_updated < start:
                old_state = new_state
                continue
            if ignore_unavailable and (
                new_state.state in IGNORED_STATES
                or (old_state is not None and old_state.state in IGNORED_STATES)
            ):
                old_state = new_state
                continue
            state_changed = old_state is None or old_state.state != new_state.state
            domain = new_state.entity_id.partition(".")[0]
            attributes_changed = include_attributes and any(
                old_state is None
                or old_state.attributes.get(name) != new_state.attributes.get(name)
                for name in SIGNIFICANT_ATTRIBUTES.get(domain, ())
            )
            if state_changed or attributes_changed:
                event = MemoryEvent.from_states(old_state, new_state).attributed(
                    origin=EventOrigin.UNKNOWN,
                    confidence="low",
                )
                restored.append(event)
            old_state = new_state
    return restored


def _query_history(
    hass: HomeAssistant,
    start: datetime,
    end: datetime,
    entity_ids: list[str],
) -> dict[str, list[State]]:
    """Run the bounded, database-portable Recorder history query."""
    return history.get_significant_states(
        hass=hass,
        start_time=start,
        end_time=end,
        entity_ids=entity_ids,
        filters=None,
        include_start_time_state=True,
        significant_changes_only=False,
        minimal_response=False,
        no_attributes=False,
        compressed_state_format=False,
    )


async def async_restore_events(
    hass: HomeAssistant,
    entity_ids: set[str],
    start: datetime,
    end: datetime,
    *,
    include_attributes: bool,
    ignore_unavailable: bool,
) -> list[MemoryEvent]:
    """Restore events through Recorder's dedicated database executor."""
    recorder = get_instance(hass)
    states = await recorder.async_add_executor_job(
        _query_history, hass, start, end, sorted(entity_ids)
    )
    return _restored_events(
        states,
        start,
        include_attributes=include_attributes,
        ignore_unavailable=ignore_unavailable,
    )
