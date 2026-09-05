<p align="center">
  <img src="https://raw.githubusercontent.com/vince87/HA-Entity-Memory/main/custom_components/entity_memory/brand/icon%402x.png" alt="Entity Memory icon" width="220" height="220">
</p>

# Entity Memory

Entity Memory gives Home Assistant automations two complementary kinds of
memory without requiring database templates or visible helper entities:

1. **Entity-event memory** remembers meaningful recent changes and their best
   available origin attribution.
2. **Persistent registers** store small automation-owned values such as phases,
   checkpoints, flags, and last-applied policies.

> [!IMPORTANT]
> This project is a beta. Entity Memory is a decision aid, not a safety system.
> Keep alarms, locks, weather protection, and other safety interlocks in normal
> Home Assistant conditions.

## Requirements and scope

- Current prerelease: `0.2.0-beta.2`
- Home Assistant 2026.x
- Recorder enabled for entity-event restoration
- One configuration entry
- Supported event domains: `light`, `cover`, `climate`, `switch`, and
  `binary_sensor`
- English, Italian, German, French, Spanish, and Portuguese interface text

## Installation

### HACS

1. Add `https://github.com/vince87/HA-Entity-Memory` as a custom **Integration**
   repository in HACS.
2. Enable prereleases and install the latest named version, currently
   `0.2.0-beta.2`.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Add integration** and select
   **Entity Memory**.

Use named prereleases for testing. Installing a branch or pull-request build
makes HACS display commit hashes instead of semantic versions. To return to the
normal release channel, use **Redownload**, explicitly select the named version,
and restart Home Assistant.

### Manual

Copy `custom_components/entity_memory` into
`/config/custom_components/entity_memory`, restart Home Assistant, and add the
integration from **Settings → Devices & services**.

## Configuration

Select concrete entities, wildcard patterns, or both. Patterns are resolved
against the entity registry and current states.

Examples:

```text
light.kitchen
cover.*
binary_sensor.*_window
```

Prefer the narrowest selection that covers the automation. Broad patterns
increase live listeners, memory use, and Recorder work.

Options control:

- the rolling event window;
- whether `unknown` and `unavailable` transitions are ignored;
- whether meaningful domain-specific attribute changes are retained.

## Entity-event memory

The event cache is bounded by the configured window. At startup it is restored
from Recorder, then updated from live Home Assistant state changes.

Available actions:

- `entity_memory.get_events`
- `entity_memory.last_event`
- `entity_memory.was_changed`
- `entity_memory.count_events`

All actions return response data and should normally use `response_variable`:

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - climate.living_room
    since: "02:00:00"
    to_state: "off"
    origins:
      - authenticated_command
      - external_or_physical
  response_variable: memory

- condition: template
  value_template: "{{ not memory.found }}"
```

### Origin attribution

Reported origins are deliberately conservative:

- `automation`: attributed through Home Assistant automation context;
- `authenticated_command`: associated with a Home Assistant user, but not
  necessarily a particular dashboard, app, or voice bridge;
- `external_or_physical`: no matching Home Assistant command was observed;
- `device_observation`: an observed sensor change;
- `unknown`: insufficient attribution data, especially after Recorder restore.

Confidence describes attribution certainty, not device-state accuracy. Do not
infer a person, client, or vendor from timing alone.

## Persistent registers

Registers are stored separately from Recorder and never appear as Home Assistant
entities. They survive restarts and integration reloads.

Available actions:

- `entity_memory.get_register`
- `entity_memory.set_register`
- `entity_memory.compare_register`
- `entity_memory.delete_register`
- `entity_memory.list_registers`

Create or update a value:

```yaml
- action: entity_memory.set_register
  data:
    key: shutters.west_floor_1
    value:
      phase: shade
      enabled: true
  response_variable: saved
```

Read it later, including after a restart:

```yaml
- action: entity_memory.get_register
  data:
    key: shutters.west_floor_1
  response_variable: register
```

The response includes `found`, `value`, `revision`, and `updated_at`. Rewriting
the same value is a no-op and preserves its revision and timestamp.

### Safe concurrent updates

Pass `expected_revision` when multiple executions may update the same key:

```yaml
- action: entity_memory.set_register
  data:
    key: shutters.west_floor_1
    value: open
    expected_revision: "{{ register.revision }}"
  response_variable: result
```

Revision `0` means the key must not exist. If the current revision differs, the
write is rejected, `result.conflict` is `true`, and the existing value remains
untouched. Omitting `expected_revision` keeps the simple unconditional behavior.

### Limits

- Lowercase keys, maximum 128 characters
- Letters, numbers, dots, underscores, and hyphens in keys
- JSON-compatible values only
- Maximum encoded value size: 16 KiB
- Maximum registers per installation: 256

Do not store passwords, tokens, personal data, large documents, or high-frequency
telemetry in registers.

## Recommended automation workflow

For periodically calculated policies:

1. Calculate the current policy.
2. Read its register.
3. Treat a missing or different value as a new program phase.
4. Apply the device action.
5. Save the policy only after the device action succeeds.
6. When the policy has not changed, consult entity-event memory before
   overriding a recent non-automation choice.

A missing register is initialization, not proof of a physical change. Decide
explicitly whether the first run should apply the calculated state or only save
it.

## Upgrading and rollback

Before testing a prerelease, back up the Home Assistant configuration. Existing
config entries remain compatible unless release notes say otherwise.

Rolling back the integration does not automatically delete registers. Older
versions simply ignore their storage. Use `delete_register` when a value should
be intentionally removed.

After an upgrade, verify the semantic version under **Settings → Devices &
services → Entity Memory**. A commit hash means HACS is still following a branch
build rather than a named release.

## Diagnostics

Open **Settings → Devices & services → Entity Memory**, open the menu for the
configured entry, and choose **Download diagnostics**. The report contains only
aggregate counts, encoded register value sizes, storage limits, and the storage
format version. It excludes tracked entity IDs, register keys, register values,
user IDs, and context IDs.

Attach diagnostics to a bug report only after reviewing the downloaded file.
Logs and automation traces are separate artifacts and may contain household
identifiers, so sanitize them before sharing.

## Troubleshooting

- Integration missing: confirm
  `/config/custom_components/entity_memory/manifest.json` exists and restart.
- Actions report that Entity Memory is unavailable: confirm the config entry is
  loaded under **Settings → Devices & services**.
- No restored events: confirm Recorder contains the selected entities inside the
  configured window.
- Raw translation keys: update the integration, restart Home Assistant, and
  refresh the browser cache.
- Register conflict: read the returned current revision, recalculate the desired
  change, and retry only if it is still appropriate.

Never publish entity IDs, user IDs, context IDs, tokens, register contents, or
database excerpts in public issues without anonymizing them.

## Documentation

- [Persistent register reference](docs/PERSISTENT_REGISTERS.md)
- [Automation-assistant guide and generation contract](docs/AI_AUTOMATION_GUIDE.md)
- [Automation patterns for covers, lights, doors, and PIR](docs/AUTOMATION_PATTERNS.md)
- [Controlled-test plan](docs/CONTROLLED_TEST_PLAN.md)
- [Stable-release checklist](docs/STABLE_RELEASE_CHECKLIST.md)
- [Reference environment](docs/REFERENCE_ENVIRONMENT.md)
- [Roadmap](ROADMAP.md)
- [Release notes](RELEASE_NOTES.md)

## License

MIT
