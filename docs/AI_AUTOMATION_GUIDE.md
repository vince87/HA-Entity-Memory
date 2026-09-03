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

