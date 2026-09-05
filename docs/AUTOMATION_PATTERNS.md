# Automation patterns

These anonymized fragments demonstrate Entity Memory query contracts. Replace
every placeholder entity and tune the look-back window for the installation.
They are decision patterns, not safety controls.

## Cover — preserve a recent uncertain position change

```yaml
- action: entity_memory.last_event
  data:
    entity_id:
      - cover.example_shutter
    since: "04:00:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: cover_memory

- condition: template
  value_template: "{{ cover_memory.event is none }}"
```

Use this only inside the current program phase. A new schedule boundary or
calculated solar phase may deliberately supersede the older choice. Absolute
alarm or weather constraints must be evaluated first.

## Light — act only when no recent non-automation command exists

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - light.example_room
    since: "00:30:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: light_memory

- condition: template
  value_template: "{{ not light_memory.found }}"
```

This conservative rule treats ambiguous changes as a reason to wait. Choose a
different policy explicitly rather than relabeling ambiguity as automation.

## Door — count openings in a bounded window

```yaml
- action: entity_memory.count_events
  data:
    entity_id:
      - binary_sensor.example_door
    since: "01:00:00"
    to_state: "on"
  response_variable: door_memory

- condition: template
  value_template: "{{ door_memory.count >= 3 }}"
```

For binary sensors, `on` and `off` retain their Home Assistant meanings. Check
the device class before describing them as open, closed, motion, or clear.

## PIR — inspect the newest motion event

```yaml
- action: entity_memory.last_event
  data:
    entity_id:
      - binary_sensor.example_motion
    since: "00:10:00"
    to_state: "on"
  response_variable: motion_memory

- condition: template
  value_template: "{{ motion_memory.event is not none }}"
```

A PIR transition is a device observation, not proof of a particular person.
Never infer identity, presence duration, or intent from this event alone.

## Multi-entity query

```yaml
- action: entity_memory.get_events
  data:
    entity_id:
      - binary_sensor.example_door
      - binary_sensor.example_motion
    since: "00:15:00"
    limit: 20
  response_variable: area_memory
```

Results are newest first. Always tolerate an empty `events` list and use the
returned `count` rather than assuming a match exists.
