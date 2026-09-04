# Reference entity profiles

These anonymized profiles define which changes are meaningful for the first
real-world test set. Entity IDs and friendly names are intentionally omitted.

## On/off light

Observed capabilities:

- `supported_color_modes: [onoff]`
- no brightness or color control

Memory policy: retain only state transitions (`on` and `off`). Attribute-only
updates are not meaningful for this profile.

## Position-aware cover

Observed capabilities:

- `current_position`
- `is_closed`

Memory policy: retain open/closed state transitions and changes to
`current_position`. The derived `is_closed` attribute does not need a separate
event when the state or position already expresses the same transition.

## Climate device

Observed capabilities:

- HVAC modes: off, automatic, cooling, heating, fan-only, and dry
- target temperature with a one-degree step
- selectable fan mode
- selectable swing mode
- current temperature measurement

Memory policy: retain HVAC state, target temperature, fan mode, swing mode, and
preset changes. Do not retain `current_temperature` changes: they are sensor
measurements rather than user intent and would create noisy history.

## Window binary sensor

Observed capabilities:

- `device_class: window`

Memory policy: retain only `on`/`off` transitions, interpreted by Home Assistant
as open/closed. Friendly-name changes are not events.

## Remaining attribution samples

For context attribution tests, each profile needs representative
`state_changed` payloads produced by:

1. a dashboard/app action;
2. an automation action;
3. a physical control or device-originated change;
4. a vendor application action, when available.

