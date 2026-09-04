# Persistent registers

Persistent registers let automations keep small JSON-compatible values without
creating helper entities. They are independent from the rolling entity-event
history and survive Home Assistant restarts.

This feature adds storage, not synthetic entities. A register has no state in
Home Assistant's state machine, cannot be selected as an entity, and does not
generate Recorder history. Automations interact with it only through actions
that return response data.

Typical uses include an automation phase, a finite-state-machine checkpoint, a
last applied policy, or a compact group of flags. Registers are not intended for
large documents, secrets, high-frequency telemetry, or safety-critical state.

Keys are lowercase names up to 128 characters. They may contain letters,
numbers, dots, underscores, and hyphens. Dots can be used as namespaces, for
example `shutters.west_floor_1`. Values must be JSON-compatible and are limited
to 16 KiB each. An installation can contain at most 256 registers.

Each stored record contains:

- `value`: the JSON-compatible value supplied by the caller;
- `revision`: starts at 1 and increases only when the value changes;
- `updated_at`: the UTC timestamp of the last actual change.

Writing an equal value is a no-op and does not increase the revision or update
the timestamp. Values are persisted through Home Assistant's integration
storage and loaded when Entity Memory starts.

## Read a register

```yaml
- action: entity_memory.get_register
  data:
    key: shutters.west_floor_1
  response_variable: register
```

The response contains `found`, `value`, `revision`, and `updated_at`. Missing
registers return `found: false`, `value: null`, and revision `0`.

## Set a register

```yaml
- action: entity_memory.set_register
  data:
    key: shutters.west_floor_1
    value:
      phase: shade
      enabled: true
  response_variable: result
```

The response also reports `created`, `changed`, and `previous`. Writing the same
value is a no-op: it does not change the timestamp or revision and does not write
storage again.

`set_register` also accepts an optional `expected_revision` for safe concurrent
updates. Revision `0` means that the key must not exist:

```yaml
- action: entity_memory.set_register
  data:
    key: shutters.west_floor_1
    value: shade
    expected_revision: "{{ register.revision }}"
  response_variable: result
```

If another execution changed the register after it was read, no write occurs and
the response contains `conflict: true` together with the current value and
revision. A successful or unconditional write returns `conflict: false`.

Valid values include strings, booleans, numbers, null, lists, and objects made
from those types. Non-JSON objects, non-finite numbers, and oversized values are
rejected.

## Compare without changing

```yaml
- action: entity_memory.compare_register
  data:
    key: shutters.west_floor_1
    value: "{{ calculated_phase }}"
  response_variable: comparison
```

`comparison.matches` is true only when the register exists and its value equals
the supplied value. This action never writes. A robust automation can compare,
perform its device actions, and call `set_register` only after they succeed.

## Periodic automation pattern

Registers are especially useful when an automation has one periodic trigger
but needs to recognize changes in a calculated policy:

```yaml
triggers:
  - trigger: time_pattern
    minutes: /5

actions:
  - variables:
      policy: >-
        {{ 'active' if is_state('binary_sensor.example', 'on') else 'idle' }}

  - action: entity_memory.get_register
    data:
      key: example.policy
    response_variable: memory

  - variables:
      policy_changed: "{{ not memory.found or memory.value != policy }}"

  # Decide and perform the external action here.

  - if:
      - condition: template
        value_template: "{{ policy_changed }}"
    then:
      - action: entity_memory.set_register
        data:
          key: example.policy
          value: "{{ policy }}"
        response_variable: saved
```

Choose initialization behavior deliberately. With `not memory.found` in the
expression above, the first run is considered a new phase. An automation that
must not act on its first run should instead save the calculated policy and stop.

When multiple executions may update the same key concurrently, either serialize
the automation (`mode: single`) or pass the revision returned by `get_register`
as `expected_revision` to `set_register`. `compare_register` and `set_register`
remain separate calls and do not form a transaction together.

## Delete and list

```yaml
- action: entity_memory.delete_register
  data:
    key: shutters.west_floor_1
  response_variable: deletion
```

```yaml
- action: entity_memory.list_registers
  data:
    prefix: shutters.
    limit: 100
  response_variable: registers
```

Registers are internal data, not Home Assistant entities. They therefore do not
appear in dashboards, entity selectors, history, or Recorder.

Deleting or re-adding the integration is not a supported register-reset
mechanism. Use `delete_register` for one key, or list a namespace and delete its
keys explicitly when an automation is retired.

Register storage belongs to the integration domain rather than to one config
entry. Removing and later re-adding the config entry therefore restores the
existing registers. This prevents accidental state loss, but it also means that
retired automation keys should be deleted explicitly.

If Home Assistant detects register storage created by an unsupported future
version, loading fails closed: Entity Memory does not expose or overwrite that
data. Install a compatible integration version rather than editing the storage
file manually.

Once a register write has entered its storage commit, caller cancellation waits
for that commit to finish before it propagates. This keeps runtime state and the
persisted value aligned during automation cancellation or shutdown.

## Diagnostics and privacy

Downloaded Home Assistant diagnostics contain only aggregate register counts,
encoded value sizes, and configured limits. Register keys and values are never
included. Tracked entity IDs are also omitted; only their total count is
reported. This makes diagnostics suitable for issue reports without publishing
automation state or household identifiers.
