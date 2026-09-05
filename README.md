<p align="center">
  <img src="https://raw.githubusercontent.com/vince87/HA-Entity-Memory/main/custom_components/entity_memory/brand/icon%402x.png" alt="Entity Memory" width="180">
</p>

<h1 align="center">Entity Memory</h1>

<p align="center">Persistent, privacy-conscious memory for Home Assistant automations.</p>

<p align="center">
  <a href="https://github.com/vince87/HA-Entity-Memory/releases"><img alt="Release" src="https://img.shields.io/github/v/release/vince87/HA-Entity-Memory?style=flat-square"></a>
  <a href="https://github.com/vince87/HA-Entity-Memory/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/vince87/HA-Entity-Memory/validate.yml?branch=main&style=flat-square&label=validation"></a>
  <a href="https://www.hacs.xyz/"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5?style=flat-square"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/vince87/HA-Entity-Memory?style=flat-square"></a>
</p>

<p align="center"><strong>English</strong> · <a href="README.it.md">Italiano</a></p>

Entity Memory adds two kinds of memory without creating visible helper entities:

- **Event memory** retains meaningful recent changes to lights, covers, climate devices, switches, and binary sensors, with conservative origin attribution.
- **Persistent registers** retain small automation-owned values, flags, phases, and checkpoints across reloads and restarts.

It answers questions such as “was this device recently changed outside my automation?” and “is this still the same calculated program phase?”.

> [!IMPORTANT]
> Entity Memory is a decision aid, not a safety system. Alarms, locks, fire, rain, wind, frost, and other safety interlocks must remain ordinary Home Assistant conditions and always take precedence over remembered preferences.

## Highlights

- Home Assistant UI configuration
- Explicit entities and wildcard patterns such as `cover.*`
- Recorder-backed restoration after restart
- Conservative origin attribution and confidence
- Response actions designed for automations
- Entity-less JSON registers with revisions and optimistic concurrency
- Privacy-safe aggregate diagnostics
- Interface translations in English, Italian, German, French, Spanish, and Portuguese

## Installation

### HACS

1. Add `https://github.com/vince87/HA-Entity-Memory` as a custom **Integration** repository in HACS.
2. Download the latest stable release.
3. Restart Home Assistant.
4. Open **Settings → Devices & services → Add integration** and select **Entity Memory**.

### Manual

Copy `custom_components/entity_memory` to `/config/custom_components/entity_memory`, restart Home Assistant, and add the integration from **Settings → Devices & services**.

Requires Home Assistant `2026.1.0` or newer. Recorder is required to restore event history after startup.

## Quick start

Choose concrete entities, wildcard patterns, or both. Prefer the narrowest useful selection.

```text
light.kitchen
cover.*
binary_sensor.*_window
```

Query whether a relevant recent change exists:

```yaml
- action: entity_memory.was_changed
  data:
    entity_id:
      - light.kitchen
    since: "00:30:00"
    origins:
      - authenticated_command
      - external_or_physical
      - unknown
  response_variable: memory

- condition: template
  value_template: "{{ not memory.found }}"
```

Remember an automation phase across runs and restarts:

```yaml
- action: entity_memory.set_register
  data:
    key: shutters.west.phase
    value: shade
  response_variable: saved
```

## Available actions

| Event memory | Persistent registers |
|---|---|
| `get_events` | `get_register` |
| `last_event` | `set_register` |
| `was_changed` | `compare_register` |
| `count_events` | `delete_register` |
| | `list_registers` |

All actions return response data and should normally use `response_variable`.

## Documentation

| English | Italiano |
|---|---|
| [AI automation guide](docs/AI_AUTOMATION_GUIDE.md) | [Guida per automazioni IA](docs/AI_AUTOMATION_GUIDE.it.md) |
| [Persistent registers](docs/PERSISTENT_REGISTERS.md) | [Registri persistenti](docs/PERSISTENT_REGISTERS.it.md) |
| [Automation patterns](docs/AUTOMATION_PATTERNS.md) | [Schemi di automazione](docs/AUTOMATION_PATTERNS.it.md) |
| [Climate example](docs/EXAMPLE_CLIMATE_AUTOMATION.md) | [Esempio climatizzazione](docs/EXAMPLE_CLIMATE_AUTOMATION.it.md) |

See [release notes](RELEASE_NOTES.md) for changes and compatibility information.

## Attribution limits

Attribution is intentionally conservative. `authenticated_command` proves that Home Assistant associated a command with a user, not whether it came from a dashboard, app, or voice bridge. `external_or_physical` can also mean an external integration. Recorder-restored events may be `unknown` with low confidence.

## Privacy and support

Diagnostics exclude entity IDs, register keys and values, user IDs, and context IDs. General logs and automation traces should still be sanitized before sharing.

When reporting a problem, include the Entity Memory version, Home Assistant version, anonymized steps, and reviewed diagnostics in the [issue tracker](https://github.com/vince87/HA-Entity-Memory/issues).

## License

[MIT](LICENSE)
