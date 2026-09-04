# Persistent registers

Persistent registers let automations keep small JSON-compatible values without
creating helper entities. They are independent from the rolling entity-event
history and survive Home Assistant restarts.

Typical uses include an automation phase, a finite-state-machine checkpoint, a
last applied policy, or a compact group of flags. Registers are not intended for
large documents, secrets, high-frequency telemetry, or safety-critical state.

Keys are lowercase names up to 128 characters. They may contain letters,
numbers, dots, underscores, and hyphens. Dots can be used as namespaces, for
example `shutters.west_floor_1`. Values must be JSON-compatible and are limited
to 16 KiB each. An installation can contain at most 256 registers.

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
