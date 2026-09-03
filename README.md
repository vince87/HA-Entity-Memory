<p align="center">
  <img src="https://raw.githubusercontent.com/vince87/HA-Entity-Memory/main/custom_components/entity_memory/brand/icon%402x.png" alt="Entity Memory icon" width="220" height="220">
</p>

# Entity Memory

Entity Memory is a custom Home Assistant integration that makes recent entity
history easy to query from automations.

Development status and next steps are tracked in the [project roadmap](ROADMAP.md).
The first real test installation is documented in the
[reference environment](docs/REFERENCE_ENVIRONMENT.md).
Use the [controlled-test plan](docs/CONTROLLED_TEST_PLAN.md) to validate this
prerelease on that installation.

For a practical automation pattern, see
[respecting a recent manual climate decision](docs/EXAMPLE_CLIMATE_AUTOMATION.md).

The intended architecture uses Home Assistant Recorder as the only persistent
source, restores a bounded in-memory cache at startup, and then follows state
changes in real time.

> [!IMPORTANT]
> This is an alpha release for controlled testing. Do not yet rely on it for
> safety, security, or unattended climate decisions.

## Initial scope

- Home Assistant 2026.x
- `light`, `cover`, `climate`, `switch`, and `binary_sensor`
- Configurable rolling window (12 hours by default)
- UI configuration and reconfiguration
- Compact wildcard selection alongside individual entities (for example
  `light.*` or `binary_sensor.*_window`). There is no hard entity limit; broad
  patterns should be used carefully because they increase memory use and
  Recorder load.
- Italian and English translations
- Query actions with response data:
  - `entity_memory.get_events`
  - `entity_memory.last_event`
  - `entity_memory.was_changed`
  - `entity_memory.count_events`

## Installation

Install the repository as a custom integration through HACS, restart Home
Assistant, then add **Entity Memory** from **Settings > Devices & services**.
For a manual installation, copy `custom_components/entity_memory` to
`/config/custom_components/entity_memory` before restarting.

When upgrading from an earlier development snapshot, update the repository in
HACS (or replace the integration directory), restart Home Assistant, and
confirm that the manifest reports `0.1.0-alpha.8`. Existing config entries are
kept because the config-flow version remains unchanged.

In the integration options, individual entities can be combined with wildcard
patterns entered one per line (commas are also accepted). Patterns must include
a supported domain, such as `light.*`, `switch.kitchen_*`, or
`binary_sensor.*_window`. Patterns are resolved from Home Assistant's entity
registry as well as its currently loaded states. Matching registry additions,
removals, and entity-ID changes refresh the selection automatically.

The integration icon is bundled locally, so it is also shown in Home
Assistant's integration screens without depending on the central brands
repository.

## Example

```yaml
- action: entity_memory.was_changed
  data:
    entity_id: climate.living_room
    since: "02:00:00"
    to_state: "off"
    origins:
      - authenticated_command
      - external_or_physical
  response_variable: memory

- condition: template
  value_template: "{{ not memory.found }}"
```

## Attribution

Home Assistant context information is useful but not always conclusive:

- a `user_id` identifies an authenticated command, but may represent the
  dashboard, an app, or a voice assistant linked to the same account;
- a `parent_id` normally identifies an automation or script chain;
- when both are absent, the source may be a physical control, device, or
  external integration.

Entity Memory correlates service calls with later device confirmations for up
to 180 seconds. It reports `external_or_physical` when no matching command is
seen, rather than claiming that the change was certainly manual. Restored
Recorder events may have `unknown` origin and low confidence because historical
state rows do not always retain enough attribution context.

When an automation action has no `parent_id`, Entity Memory cross-checks the
exact context ID emitted by Home Assistant's `automation_triggered` event. It
does not infer automation attribution from timing alone, so unrelated commands
that happen close together remain unclassified.

## Troubleshooting

- If the integration does not appear, confirm that
  `/config/custom_components/entity_memory/manifest.json` exists and restart
  Home Assistant.
- If an action reports that Entity Memory is not loaded, check the integration
  entry under **Settings > Devices & services** and inspect the Home Assistant
  log for setup errors.
- If no historical events appear after restart, confirm that Recorder includes
  the selected entities and contains rows inside the configured window.
- Do not report entity IDs, user IDs, context IDs, tokens, or database contents
  in public issues; anonymize diagnostic examples first.

## License

MIT
