<p align="center">
  <img src="assets/entity-memory-icon.svg" alt="Entity Memory icon" width="220" height="220">
</p>

# Entity Memory

Entity Memory is a custom Home Assistant integration that makes recent entity
history easy to query from automations.

Development status and next steps are tracked in the [project roadmap](ROADMAP.md).

The intended architecture uses Home Assistant Recorder as the only persistent
source, restores a bounded in-memory cache at startup, and then follows state
changes in real time.

> [!IMPORTANT]
> This first alpha scaffold currently collects and queries live changes. The
> Recorder restore path is not implemented yet because Home Assistant's normal
> History API does not preserve all context attribution fields. Do not install
> this snapshot on a production system yet.

## Initial scope

- Home Assistant 2026.x
- `light`, `cover`, `climate`, `switch`, and `binary_sensor`
- Configurable rolling window (12 hours by default)
- UI configuration and reconfiguration
- Italian and English translations
- Query actions with response data:
  - `entity_memory.get_events`
  - `entity_memory.last_event`
  - `entity_memory.was_changed`
  - `entity_memory.count_events`

## Installation (development snapshot)

Copy `custom_components/entity_memory` into the Home Assistant configuration
directory, restart Home Assistant, then add **Entity Memory** from
**Settings > Devices & services**.

This repository is an early development snapshot. Validate it in a test Home
Assistant instance before relying on it for climate or security automations.

## Example

```yaml
- action: entity_memory.was_changed
  data:
    entity_id: climate.living_room
    since: "02:00:00"
    to_state: "off"
    origins:
      - user
      - device_or_external
  response_variable: memory

- condition: template
  value_template: "{{ not memory.found }}"
```

## Attribution

Home Assistant context information is useful but not always conclusive:

- a `user_id` normally identifies a dashboard/app user;
- a `parent_id` normally identifies an automation or script chain;
- when both are absent, the source may be a physical control, device, or
  external integration.

Entity Memory therefore reports `device_or_external` instead of claiming that
such events are certainly manual.

## License

MIT

