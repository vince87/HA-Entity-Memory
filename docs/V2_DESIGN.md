# Entity Memory v2: compatibility and design

Baseline: upstream `b5667724454c1b8955832e057e79bcfc4eb6411c` (0.2.0),
preserved on `pre-2026.9`. Target: Home Assistant 2026.9.0 and 2026.9.1.

## Public contract audited before implementation

`entity_memory.was_changed` is a **response action**, not a Jinja function.
The existing implementation does not expose `entity_memory.was_changed(...)`
inside templates. Existing automation YAML should remain unchanged:

```yaml
- action: entity_memory.was_changed
  data:
    entity_id: cover.tapparella_portafinestra
    since: "00:30:00"
    origins:
      - authenticated_command
      - external_or_physical
  response_variable: memory
- condition: template
  value_template: "{{ not memory.found }}"
```

All four query actions retain `entity_id`, `since` (12 hours by default),
`to_state`, `origins` and `limit` (100 by default, 1–1000). Results are newest
first. `get_events` returns `events` and `count`; `last_event` returns `event`;
`was_changed` returns `found` and `event`; `count_events` returns `count`.
Counts remain limited by `limit`, including the existing count_events behavior.
Missing-event responses and serialized event fields remain unchanged.

The five origin strings remain `automation`, `authenticated_command`,
`external_or_physical`, `device_observation`, `unknown`. Confidence strings
remain `high`, `medium`, `low`. Better native evidence can improve classification
of individual events; the vocabulary and filtering contract are unchanged.

All five register actions, keys, JSON values, revision/conflict rules, limits,
storage key `entity_memory.registers` and storage version 1 remain unchanged.
No migration touches register files or the user's automation configuration.
Existing config entries remain version 1 with their selected entities and window.

## Comparison with HA 2026.9

Sources reviewed:

- [Core 2026.9.0 logbook processor](https://github.com/home-assistant/core/blob/2026.9.0/homeassistant/components/logbook/processor.py)
- [Core 2026.9.1 logbook processor](https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/components/logbook/processor.py)
- [Core 2026.9.1 live logbook subscriptions](https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/components/logbook/websocket_api.py)

Logbook retains context relationships and parent user IDs, and fetches additional
Recorder context rows for historical attribution. Its output is an activity
presentation: continuous sensors and some changes are filtered. It is not a
drop-in replacement for Entity Memory's complete significant-change queries.
Context IDs already existed before 2026.9; they are not a newly introduced store.

The original component already used only RAM for event history and read Recorder
on startup. There was **no duplicate event-history database to remove**. v2 keeps
that property and avoids restoring every selected entity at startup.

## Native live attribution

The component observes `call_service`, `automation_triggered` and `script_started`.
A 4096-entry context cache follows up to 32 parent links, rejecting cycles and
evidence older than one hour. Exact ancestry precedes legacy value correlation.
Automation/script evidence maps to the existing `automation` origin; an inherited
user without such evidence maps to `authenticated_command`. This also supports
service calls targeting areas or devices when HA propagates their context.
The state's context ID and parent ID are preserved for native matches.

An observed anonymous HA service chain remains `unknown`, rather than being
claimed as physical. A change with no attributable HA cause falls back to the
existing external/physical or binary-sensor observation behavior. Sensors newly
selected in v2 use `device_observation`. Neither external/physical nor a user ID
proves a physical button press or a particular app.

For devices that discard context, the previous 180-second value correlation is
retained for compatibility, with bounded per-entity intent queues and guards
against future commands or conflicting explicit ancestry. This is still an
inference. Existing parent-only classification is retained as a fallback; an
unresolved parent alone is not new proof of which automation ran. v2 does not
claim identical attribution to Activity for every integration.

## RAM, selection and Recorder

Use `*` or `*.*` to select every domain, with optional exclusion patterns such as
`sensor.*`, `update.*` or an individual entity ID. Existing fnmatch syntax remains
valid. A single state listener applies selection dynamically, so new entities do
not reload the component or reset live attribution. Attribute significance for
the original domains is unchanged; added domains capture state transitions.

Event payloads are compressed JSON held only in RAM. Timestamp, state and origin
remain directly searchable; only selected results are decoded. Global expiration
runs periodically rather than scanning every entity for every incoming event.
The complete time window is retained. RAM scales with event rate and window
length, not a fixed 5–20-event cap. This is deliberate: dropping an older manual
event can turn an existing `was_changed` result into a false negative. Exclusions
and shorter configured windows remain useful for high-rate telemetry.

On the first query for an entity, Recorder reconstructs the portion of the window
before setup. Queries use Recorder's executor, are bounded by entity and time,
and are serialized to avoid duplicate concurrent restorations. Live events win
when merged with restored rows. Failures are surfaced and can be retried; no
failure is converted into a false "not changed" result. Registers load without
an eager history query.

Recorder history rows remain `unknown`/low confidence as in 0.2.0. Logbook's
filtered UI output cannot safely replace those rows, and v2 does not add a private
SQL schema dependency to guess their origin. Recorder exclusions and retention
still limit available history. No historical causal restoration is claimed.

## Verification and rollout

Regression tests cover existing action schemas/responses, origins, state and
attribute significance, register persistence/concurrency, history restoration
and merge semantics. Added tests exercise ancestry, unrelated user commands,
script chains, cache capacity/expiry/cycles, dynamic entity capture/exclusion,
unload cleanup, lazy restoration and old manual events after 2000 later changes.
CI tests both HA 2026.9.0 and 2026.9.1 and runs Ruff, Hassfest and HACS validation.

This is a development beta, not a claim of a completed soak test in the user's
running installation. The HA instance and its automations are not modified.
Before a stable release, validate dashboard, automation and physical controls on
the actual devices, then reload/restart and check register persistence. Rollback
uses the existing 0.2.0 release or `pre-2026.9`; register format is unchanged.
