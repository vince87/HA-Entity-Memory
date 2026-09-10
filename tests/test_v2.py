"""Native ancestry, compact history and compatible service queries."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from homeassistant.core import Context, Event

from custom_components.entity_memory import EntityMemoryRuntime, _register_actions
from custom_components.entity_memory.contexts import ContextCache
from custom_components.entity_memory.correlation import IntentTracker
from custom_components.entity_memory.models import (
    EventConfidence,
    EventOrigin,
    MemoryEvent,
)
from custom_components.entity_memory.selection import selected
from custom_components.entity_memory.store import EventStore

NOW = datetime(2026, 9, 10, tzinfo=UTC)


def change(context_id=None, parent_id=None, user_id=None):
    return MemoryEvent(
        "cover.test",
        NOW,
        "closed",
        "open",
        EventOrigin.UNKNOWN,
        context_id=context_id,
        parent_id=parent_id,
        user_id=user_id,
    )


def cause(kind, context):
    return Event(
        kind,
        {"domain": "cover", "service": "open_cover"},
        context=context,
        time_fired_timestamp=NOW.timestamp(),
    )


def test_parent_user_and_area_target_need_no_entity_target():
    cache = ContextCache()
    cache.observe(cause("call_service", Context(id="root", user_id="user")))
    event = cache.resolve(change("child", "root"))
    assert event.origin == EventOrigin.AUTHENTICATED_COMMAND
    assert event.context_id == "child"
    assert event.parent_id == "root"
    assert event.user_id == "user"


def test_automation_and_nested_script_override_ancestor_user():
    cache = ContextCache()
    cache.observe(cause("call_service", Context(id="user", user_id="person")))
    cache.observe(cause("automation_triggered", Context(id="auto", parent_id="user")))
    cache.observe(cause("script_started", Context(id="script", parent_id="auto")))
    cache.observe(cause("call_service", Context(id="script", parent_id="auto")))
    event = cache.resolve(change("device", "script"))
    assert event.origin == EventOrigin.AUTOMATION
    assert event.user_id == "person"


def test_unrelated_commands_do_not_claim_a_native_user_change():
    cache = ContextCache()
    cache.observe(cause("automation_triggered", Context(id="auto")))
    event = cache.resolve(change("independent", user_id="person"))
    assert event.origin == EventOrigin.AUTHENTICATED_COMMAND
    assert cache.resolve(change("unlinked")) is None


def test_context_cycles_expiry_and_capacity():
    cache = ContextCache(capacity=2)
    cache.observe(cause("call_service", Context(id="a", parent_id="b")))
    cache.observe(cause("call_service", Context(id="b", parent_id="a")))
    assert cache.resolve(change("a")).origin == EventOrigin.UNKNOWN
    assert (
        cache.resolve(replace(change("a"), timestamp=NOW + timedelta(hours=2))) is None
    )
    cache.observe(cause("call_service", Context(id="c")))
    assert len(cache._causes) == 2
    assert "a" not in cache._causes


def test_all_entities_exclusions_and_dynamic_membership():
    assert selected("lock.new", set(), ["*"], [])
    assert selected("sensor.new", set(), ["*.*"], [])
    assert not selected("sensor.new", set(), ["*"], ["sensor.*"])
    assert not selected("cover.test", {"cover.test"}, [], ["cover.*"])


def test_compact_history_preserves_old_matching_event_and_limit():
    store = EventStore(timedelta(hours=12))
    manual = replace(
        change(),
        timestamp=NOW - timedelta(hours=1),
        origin=EventOrigin.AUTHENTICATED_COMMAND,
    )
    store.add(manual, NOW)
    for i in range(2000):
        store.add(
            replace(
                change(),
                timestamp=NOW + timedelta(microseconds=i),
                origin=EventOrigin.AUTOMATION,
            ),
            NOW,
        )
    assert store.query(
        ["cover.test"],
        NOW - timedelta(hours=2),
        origins={EventOrigin.AUTHENTICATED_COMMAND},
        limit=1,
    ) == [manual]
    assert len(store.query(["cover.test"], NOW - timedelta(hours=2), limit=100)) == 100


@pytest.mark.asyncio
async def test_lazy_restore_only_requested_entities_and_preserves_live(monkeypatch):
    from custom_components import entity_memory as integration

    store = EventStore(timedelta(hours=12))
    live = replace(change(), origin=EventOrigin.AUTHENTICATED_COMMAND)
    store.add(live, NOW)
    runtime = EntityMemoryRuntime(
        store, IntentTracker(), {"cover.test", "sensor.other"}, SimpleNamespace(), NOW
    )
    restore = AsyncMock(return_value=[change()])
    monkeypatch.setattr(integration, "async_restore_events", restore)
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: NOW)
    await runtime.async_prepare(None, ["cover.test"])
    await runtime.async_prepare(None, ["cover.test"])
    assert restore.await_count == 1
    assert restore.call_args.args[1] == {"cover.test"}
    assert store.query(["cover.test"], NOW) == [live]


@pytest.mark.asyncio
async def test_public_was_changed_response_and_origin_filter(monkeypatch):
    from custom_components import entity_memory as integration

    store = EventStore(timedelta(hours=12))
    store.add(
        replace(
            change(),
            origin=EventOrigin.EXTERNAL_OR_PHYSICAL,
            confidence=EventConfidence.MEDIUM,
        ),
        NOW,
    )
    runtime = EntityMemoryRuntime(
        store, IntentTracker(), {"cover.test"}, SimpleNamespace()
    )
    actions = {}

    def register(domain, name, handler, **kwargs):
        actions[name] = (handler, kwargs["schema"])

    hass = SimpleNamespace(
        config_entries=SimpleNamespace(
            async_loaded_entries=lambda _: [SimpleNamespace(runtime_data=runtime)]
        ),
        services=SimpleNamespace(async_register=register),
    )
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: NOW)
    _register_actions(hass)
    handler, schema = actions["was_changed"]
    data = schema(
        {
            "entity_id": "cover.test",
            "since": "00:30:00",
            "origins": ["external_or_physical"],
        }
    )
    result = await handler(SimpleNamespace(data=data))
    assert set(result) == {"found", "event"}
    assert result["found"] is True
    assert result["event"]["origin"] == "external_or_physical"


@pytest.mark.asyncio
async def test_setup_dynamic_capture_exclusions_and_unload(monkeypatch):
    from homeassistant.core import State

    from custom_components import entity_memory as integration

    listeners = {}
    cleanup = []

    def listen(kind, handler):
        listeners[kind] = handler
        return lambda: listeners.pop(kind)

    monkeypatch.setattr(
        integration,
        "Store",
        lambda *args: SimpleNamespace(async_load=AsyncMock(return_value=None)),
    )
    monkeypatch.setattr(
        integration.er, "async_get", lambda _: SimpleNamespace(entities={})
    )
    monkeypatch.setattr(
        integration, "async_track_time_interval", lambda *args: lambda: None
    )
    restore = AsyncMock(return_value=[])
    monkeypatch.setattr(integration, "async_restore_events", restore)
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: NOW)
    entry = SimpleNamespace(
        data={"entity_patterns": "*", "exclude_patterns": "sensor.*"},
        options={},
        async_on_unload=cleanup.append,
        add_update_listener=lambda _: lambda: None,
    )
    hass = SimpleNamespace(
        states=SimpleNamespace(async_entity_ids=lambda: []),
        bus=SimpleNamespace(async_listen=listen),
        config_entries=SimpleNamespace(async_update_entry=lambda *args, **kwargs: None),
    )
    assert await integration.async_setup_entry(hass, entry)
    restore.assert_not_awaited()
    context = Context(id="command", user_id="person")
    listeners["call_service"](cause("call_service", context))

    def fire(entity_id, context):
        old = State(entity_id, "closed", last_updated=NOW)
        new = State(entity_id, "open", last_updated=NOW, context=context)
        listeners["state_changed"](
            Event(
                "state_changed",
                {
                    "entity_id": entity_id,
                    "old_state": old,
                    "new_state": new,
                },
                context=context,
                time_fired_timestamp=NOW.timestamp(),
            )
        )

    fire("cover.new", context)
    fire("cover.physical", Context())
    fire("sensor.excluded", Context())
    assert (
        entry.runtime_data.store.query(["cover.new"], NOW)[0].origin
        == EventOrigin.AUTHENTICATED_COMMAND
    )
    assert (
        entry.runtime_data.store.query(["cover.physical"], NOW)[0].origin
        == EventOrigin.EXTERNAL_OR_PHYSICAL
    )
    assert entry.runtime_data.store.query(["sensor.excluded"], NOW) == []
    assert "cover.new" in entry.runtime_data.entity_ids
    for unsubscribe in cleanup:
        unsubscribe()
    assert listeners == {}
