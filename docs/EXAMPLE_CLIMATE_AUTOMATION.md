# Example: respect a recent manual climate decision

**English** · [Italiano](EXAMPLE_CLIMATE_AUTOMATION.it.md)

This example shows how an automation can use Entity Memory before cooling a
room. When the temperature rises above 27 °C, it checks the most recent event
for an imaginary climate entity. It does not turn the unit back on when the
latest remembered action was a recent non-automation shutdown.

Replace the example entity IDs and temperatures with values suitable for the
installation. This is a behavioral example, not a safety control.

```yaml
alias: Example - cool only when not recently stopped manually
description: Respect the latest remembered climate decision.
triggers:
  - trigger: numeric_state
    entity_id: sensor.example_room_temperature
    above: 27

conditions:
  - condition: state
    entity_id: climate.example_air_conditioner
    state: "off"

actions:
  - action: entity_memory.last_event
    data:
      entity_id:
        - climate.example_air_conditioner
      since: "02:00:00"
    response_variable: climate_memory

  - condition: template
    alias: Continue unless the latest event was a non-automation shutdown
    value_template: >-
      {{ climate_memory.event is none
         or climate_memory.event.new_state != 'off'
         or climate_memory.event.origin == 'automation' }}

  - action: climate.set_temperature
    target:
      entity_id: climate.example_air_conditioner
    data:
      hvac_mode: cool
      temperature: 24

mode: single
```

The decision is intentionally conservative:

- no remembered event means the automation may continue;
- a recent `automation` shutdown may be superseded by this automation;
- a recent `authenticated_command`, `external_or_physical`, or `unknown`
  shutdown prevents automatic restart;
- the two-hour `since` window defines how long the previous decision is
  respected.

Recorder-restored events can be `unknown` with low confidence. Treating a
restored shutdown as a reason not to restart avoids silently overriding a
possibly manual decision after Home Assistant restarts.
