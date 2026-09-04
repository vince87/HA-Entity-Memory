# Entity Memory guide for automation assistants

This document is the machine-readable usage contract for Entity Memory
`0.2.0-beta.2`. An AI assistant generating Home Assistant automations should
follow these rules and must not infer more attribution certainty than the
returned data provides.

## Required design order

Generate automation logic in this order:

1. **Absolute safety constraints** — alarms, locks, fire, rain, wind, frost, or
   another user-declared interlock. These override remembered preferences.
2. **Program events** — a schedule boundary or a calculated phase transition.
3. **Remembered human or uncertain choices** — preserve them until the next
   program event when the user requests that policy.
4. **Convenience behavior** — polling, retries, notifications, and cosmetic
   adjustments.

Entity Memory helps with steps 2 and 3; it must never weaken step 1. If the user
says an alarm is absolute, check it before any manual-override suppression and
apply its action even when the latest change was manual or uncertain.

Before writing YAML, obtain or explicitly mark assumptions for:

- every entity ID and the intended action for it;
- absolute constraints and their active states, including transitional states
  such as `arming` when relevant;
- scheduled boundaries and calculated phase rules;
- how long a remembered choice remains authoritative;
- startup behavior when history or a register is missing;
- automation mode and the expected behavior of overlapping runs.

## Purpose and scope

Entity Memory stores meaningful state and selected attribute changes for
configured entities in the `light`, `cover`, `climate`, `switch`, and
`binary_sensor` domains. It restores a bounded window from Recorder and follows
new changes live. It is a decision aid for automations, not a safety system.

Before generating an automation, replace all example entity IDs, thresholds,
durations, modes, and setpoints with values explicitly supplied or approved by
the user. Never publish real entity IDs, user IDs, context IDs, or tokens.

## Available actions

All actions return response data and should normally be called with
`response_variable`.

### `entity_memory.get_events`

Returns matching events newest first.

```yaml
- action: entity_memory.get_events
  data:
    entity_id:
      - climate.example_air_conditioner
    since: "02:00:00"
    origins:
      - authenticated_command
      - external_or_physical
    limit: 20
  response_variable: memory
```

Response shape: `memory.events` is a list and `memory.count` is its length.

### `entity_memory.last_event`

Returns the newest matching event.

```yaml
- action: entity_memory.last_event
  data:
    entity_id:
      - climate.example_air_conditioner
    since: "02:00:00"
  response_variable: memory
```

Response shape: `memory.event` is an event object or `none`, and
`memory.found` is a boolean.

### `entity_memory.was_changed`

Answers whether at least one matching event exists.

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - climate.example_air_conditioner
    since: "02:00:00"
    to_state: "off"
    origins:
      - authenticated_command
      - external_or_physical
  response_variable: memory
```

Response shape: `memory.found` is a boolean and `memory.event` contains the
newest match when found.

### `entity_memory.count_events`

Counts matching events. Response shape: `memory.count` is an integer.

## Persistent registers

Persistent registers are named, entity-less values for automation state. They
solve a different problem from the entity-event history:

- event history answers what changed, when, and with which attribution;
- registers remember an automation's own phase, checkpoint, flags, or last
  applied policy.

Registers survive Home Assistant restarts but do not create helper entities.
They are stored by the integration, not in Recorder, and do not appear in the
entity registry, dashboards, or history.

Use registers for small JSON-compatible values that change infrequently. Do not
use them for secrets, safety state, large documents, counters updated many times
per minute, or telemetry.

### Available register actions

- `entity_memory.get_register` reads a key;
- `entity_memory.set_register` creates or replaces a value;
- `entity_memory.compare_register` compares without writing;
- `entity_memory.delete_register` removes a key;
- `entity_memory.list_registers` returns keys, optionally under a prefix.

Every register action returns response data and should normally use
`response_variable`. Prefer readable namespaced keys such as
`shutters.west_floor_1`; do not encode several unrelated meanings into an
undocumented bitmask.

Home Assistant automation variables exist only for the current run. They are
lost when that run ends and cannot remember a decision across a later trigger,
automation reload, or Home Assistant restart. Use a register when the value must
outlive one execution; use a normal variable for calculations inside one run.

### Recommended phase-change pattern

An automation that polls periodically can use a register to turn a calculated
condition transition into a program event. This is useful when the transition
time is variable, for example a solar threshold.

1. Calculate the current policy or phase.
2. Read its register.
3. Treat a missing or different value as a new program event.
4. Apply the intended device actions.
5. Write the new phase only after those actions succeed.
6. If the phase is unchanged, preserve any relevant recent non-automation
   decision found in entity-event history.

```yaml
- variables:
    calculated_phase: >-
      {{ 'shade' if states('sensor.example_level') | float(0) > 50
         else 'open' }}

- action: entity_memory.get_register
  data:
    key: example_cover.solar_phase
  response_variable: phase_memory

- variables:
    phase_changed: >-
      {{ not phase_memory.found
         or phase_memory.value != calculated_phase }}

# Apply the device action here. A phase change may supersede an older manual
# choice; an unchanged phase should still consult entity-event memory.

- if:
    - condition: template
      value_template: "{{ phase_changed }}"
  then:
    - action: entity_memory.set_register
      data:
        key: example_cover.solar_phase
        value: "{{ calculated_phase }}"
      response_variable: phase_saved
```

A missing register is initialization, not evidence that a policy changed in the
physical world. The automation must explicitly choose whether initialization
should apply its calculated state or merely record it.

### Manual choice until the next program event

For the common rule “a manual position remains until the next scheduled or
calculated event”, do not store a permanent manual-override flag. Instead:

1. derive the current program phase;
2. compare it with the last successfully applied phase stored in a register;
3. when the phase changed, apply the new program action and save the phase;
4. when the phase did not change, query recent event memory and preserve a
   non-automation or uncertain position change;
5. always evaluate absolute constraints before this logic.

This also handles events with no predictable clock time, such as west-facing
solar shading. Represent the calculated condition as a phase (`shade`, `open`,
or another user-approved state). A threshold crossing changes the phase and is
therefore the next program event. A periodic trigger every five or ten minutes
can evaluate all phases in one automation; a separate trigger for every
possible transition is unnecessary.

Do not use time since the last run as a substitute for a phase transition. A
restart, delay, or temporary sensor outage must not manufacture a new program
event.

`compare_register` never writes. This separation is intentional: compare,
perform the external action, and save afterward so a failed device action does
not get recorded as successfully applied.

When separate executions can update the same key, pass the revision returned by
`get_register` as `expected_revision` to `set_register`. Revision `0` means the
key must still be absent. A stale revision produces `conflict: true` and leaves
the current value untouched; automation authors must handle that response rather
than assuming the write succeeded.

`expected_revision` accepts a non-negative integer or a string containing only
decimal digits, which supports templated Home Assistant values. It rejects
booleans, negative values, fractional numbers (including `1.0`), and non-numeric
strings. `compare_register` accepts only `key` and `value`; do not pass
`expected_revision` to it.

See [`PERSISTENT_REGISTERS.md`](PERSISTENT_REGISTERS.md) for exact response
shapes, persistence behavior, limits, and additional examples.

Filters may include entity, time window, old state, new state, and origin as
documented by the integration's action selector. Prefer the narrowest useful
time window.

## Event object

An event can contain:

- `entity_id`, `timestamp`, `old_state`, and `new_state`;
- `old_attributes`, `new_attributes`, and a `changes` mapping;
- `origin`, `confidence`, and `matched_service`;
- `context_id`, `parent_id`, and `user_id` when Home Assistant provides them.

Treat missing keys and null values as normal. Use defensive templates such as
`memory.event is none` before reading event fields.

## Stable contracts and best-effort fields

The action names, response container fields, newest-first ordering, register
revision rules, and missing-data responses documented here are stable public
contracts. A missing event is represented by `event: null`; a missing register
uses `found: false`, `value: null`, revision `0`, and `updated_at: null`.

Origin attribution, confidence, context identifiers, user identifiers, and
`matched_service` are best-effort observations derived from the information
Home Assistant and the device integration make available. They can be absent or
less precise after Recorder restoration, delayed device confirmation, or an
external state update. Automations must therefore remain safe when these fields
are null, `unknown`, or ambiguous.

## Origin and confidence rules

- `automation`: attributed to an automation through Home Assistant context or
  exact-context correlation.
- `authenticated_command`: a command associated with a Home Assistant user.
  It does not prove whether the actor was the dashboard, an app, or a voice
  bridge using that account.
- `external_or_physical`: no matching Home Assistant command was observed. It
  may be physical or supplied by an external integration; do not label it as
  certainly manual.
- `device_observation`: an observed sensor change rather than a command.
- `unknown`: attribution is unavailable, especially after Recorder restore.

`high`, `medium`, and `low` express attribution confidence, not device-state
accuracy. Never invent an actor from timing, friendly names, vendor names, or
nearby automation traces. Never treat `unknown` as proof that a person acted.

## Recommended decision pattern

When an automation could override a person's recent choice, default to a
conservative rule:

1. query the latest relevant event inside a bounded window;
2. allow the action when no relevant event exists;
3. allow an explicitly automated prior action when that matches the intended
   policy;
4. block or request confirmation for recent `authenticated_command`,
   `external_or_physical`, or `unknown` events;
5. keep normal Home Assistant conditions and safety interlocks separate from
   Entity Memory.

When a constraint is absolute, invert steps 2–4: satisfy that constraint first,
then use memory only when choosing among actions still allowed by it.

The complete climate example is in
[`EXAMPLE_CLIMATE_AUTOMATION.md`](EXAMPLE_CLIMATE_AUTOMATION.md).

## Template guidance

Prefer:

```jinja2
{{ memory.event is none
   or memory.event.new_state != 'off'
   or memory.event.origin == 'automation' }}
```

Avoid rules based solely on `user_id`, because multiple clients can share one
Home Assistant account. Avoid looking directly in Recorder or automation trace
storage: use Entity Memory's public actions so generated automations remain
portable and compatible with future integration changes.

## Configuration assumptions

The queried entity must be selected by the integration, directly or through a
wildcard such as `climate.*`. Wildcards affect which entities are monitored;
action calls should still name the concrete entity whose history is needed.
Broad wildcards can increase memory and Recorder load, so suggest the narrowest
pattern that satisfies the user's goal.

After configuration changes, verify the integration is loaded and run a small
live test. Restored historical events intentionally have `unknown` origin and
low confidence when Recorder lacks sufficient context.

## Generated-automation review checklist

Before presenting YAML, an AI assistant must verify that:

- all identifiers are user-provided or visibly marked placeholders;
- every response action has a `response_variable`;
- templates handle `event: null`, `found: false`, and missing best-effort fields;
- a register is saved only after the corresponding external action succeeds;
- stale register writes check `conflict` and do not silently retry forever;
- missing registers have an explicit initialization policy;
- absolute constraints cannot be bypassed by remembered manual choices;
- `unknown` and `external_or_physical` are not described as certainly manual;
- polling frequency is reasonable and registers are not used for telemetry;
- automation variables are not mistaken for persistent state;
- the automation uses `mode: single`, `restart`, `queued`, or `parallel`
  deliberately;
- rollback and cleanup identify the register namespace owned by the automation.

If any item is unknown and materially changes behavior, ask the user rather
than inventing it.

## Diagnostics contract

Home Assistant config-entry diagnostics are safe by construction: they contain
aggregate tracked-entity counts, register counts, encoded value sizes, limits,
and the register storage version. They do not contain entity IDs, register
keys, register values, user IDs, or context IDs. Do not assume the same privacy
properties for general Home Assistant logs or automation traces; sanitize those
separately before sharing.

