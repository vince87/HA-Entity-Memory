"""Exclusion-only UI, conservative defaults and upgrade compatibility."""

from types import SimpleNamespace

import pytest

from custom_components.entity_memory.config_flow import (
    EntityMemoryConfigFlow,
    EntityMemoryOptionsFlow,
    _schema,
    _submitted,
)
from custom_components.entity_memory.selection import (
    DEFAULT_EXCLUDE_PATTERNS,
    all_entities_config,
    parse_patterns,
    selected,
)


def test_form_has_exclusions_only_and_works_without_inclusions():
    defaults = all_entities_config({}, [])
    schema = _schema(defaults)
    keys = {str(key) for key in schema.schema}
    assert "exclude_entities" not in keys
    assert "exclude_patterns" in keys
    assert "entities" not in keys
    assert "entity_patterns" not in keys
    values = schema({})
    assert parse_patterns(values["exclude_patterns"]) == list(DEFAULT_EXCLUDE_PATTERNS)


def test_defaults_filter_only_named_technical_telemetry():
    patterns = list(DEFAULT_EXCLUDE_PATTERNS)
    for entity_id in [
        "update.ha",
        "sensor.radio_rssi",
        "sensor.node_uptime",
        "sensor.node_last_seen",
    ]:
        assert not selected(entity_id, set(), ["*"], patterns)
    for entity_id in [
        "sensor.temperature",
        "sensor.house_power",
        "sensor.node_battery",
        "binary_sensor.window",
        "climate.first_floor",
        "cover.window",
    ]:
        assert selected(entity_id, set(), ["*"], patterns)


def test_upgrade_expands_selection_without_dropping_previously_watched_entities():
    config = {
        "entities": ["sensor.node_rssi"],
        "entity_patterns": "light.*",
        "exclude_patterns": "sensor.custom_noise",
        "window_hours": 24,
    }
    result = all_entities_config(
        config, ["sensor.node_rssi", "light.room", "cover.new"]
    )
    assert result["entity_patterns"] == "*"
    assert result["window_hours"] == 24
    patterns = parse_patterns(result["exclude_patterns"])
    assert "sensor.custom_noise" in patterns
    assert "sensor.*_rssi" not in patterns
    assert selected("sensor.node_rssi", set(), ["*"], patterns)
    assert selected("cover.new", set(), ["*"], patterns)
    assert config["entity_patterns"] == "light.*"
    assert all_entities_config(result, []) == result


def test_explicit_old_exclusions_are_preserved_and_clearing_is_persistent():
    config = {"entities": ["sensor.node_rssi"], "exclude_patterns": "sensor.*_rssi"}
    assert "sensor.*_rssi" in parse_patterns(
        all_entities_config(config, [])["exclude_patterns"]
    )
    cleared = _submitted({"exclude_patterns": ""})
    assert all_entities_config(cleared, ["sensor.node_rssi"])["exclude_patterns"] == ""


@pytest.mark.asyncio
async def test_setup_flow_accepts_empty_selection_and_reports_exclusion_errors(
    monkeypatch,
):
    from custom_components.entity_memory import config_flow

    flow = EntityMemoryConfigFlow()
    flow.hass = SimpleNamespace()
    monkeypatch.setattr(flow, "_async_current_entries", lambda: [])
    monkeypatch.setattr(config_flow, "_available_entity_ids", lambda _: [])
    result = await flow.async_step_user({"exclude_patterns": "bad pattern"})
    assert result["errors"] == {"exclude_patterns": "invalid_entity_patterns"}
    result = await flow.async_step_user({"exclude_patterns": ""})
    assert result["data"]["selection_mode"] == "all"
    assert result["data"]["exclude_patterns"] == ""


@pytest.mark.asyncio
async def test_options_saves_exact_entity_id_as_pattern(monkeypatch):
    flow = EntityMemoryOptionsFlow()
    entry = SimpleNamespace(
        data={"entities": ["climate.floor"], "entity_patterns": "cover.*"}, options={}
    )
    monkeypatch.setattr(
        EntityMemoryOptionsFlow, "config_entry", property(lambda _: entry)
    )
    result = await flow.async_step_init({"exclude_patterns": "sensor.noise"})
    assert "exclude_entities" not in result["data"]
    assert result["data"]["entity_patterns"] == "*"
    assert result["data"]["exclude_patterns"] == "sensor.noise"
