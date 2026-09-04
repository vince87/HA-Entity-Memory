# Entity Memory guide for automation assistants

This document is the machine-readable usage contract for Entity Memory. An AI
assistant generating Home Assistant automations should follow these rules and
must not infer more attribution certainty than the returned data provides.

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

`compare_register` never writes. This separation is intentional: compare,
perform the external action, and save afterward so a failed device action does
not get recorded as successfully applied.

When separate executions can update the same key, pass the revision returned by
`get_register` as `expected_revision` to `set_register`. Revision `0` means the
key must still be absent. A stale revision produces `conflict: true` and leaves
the current value untouched; automation authors must handle that response rather
than assuming the write succeeded.

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

