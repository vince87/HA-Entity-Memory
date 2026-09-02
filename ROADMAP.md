# Entity Memory roadmap

This roadmap is the project status index. Detailed acceptance criteria and
discussion live in the linked GitHub issues.

Status legend: ⬜ planned · 🟨 in progress · ✅ complete · ⛔ blocked

## Current status

The controlled-test alpha now includes live capture, bounded Recorder restore,
command-to-state correlation, query actions, UI configuration, translations,
and local Home Assistant brand icons. The Recorder, config-entry, event-listener,
response-action, manifest, and local-brand APIs have been checked against the
Home Assistant Core 2026.8.3 source. Static validation passes; installation and
behavior still need validation on the reference container before this can
advance beyond alpha.

## Work plan

| Phase | Status | Work item | Exit condition |
|---|---|---|---|
| 1 | 🟨 | [#1 Harden live event capture](https://github.com/vince87/HA-Entity-Memory/issues/1) | Supported domains produce deduplicated, meaningful events with tests. |
| 2 | 🟨 | [#2 Implement Recorder restoration](https://github.com/vince87/HA-Entity-Memory/issues/2) | The 12-hour cache survives restarts with the best attribution Recorder can provide. |
| 3 | 🟨 | [#3 Finalize query actions](https://github.com/vince87/HA-Entity-Memory/issues/3) | Automations can reliably query, find and count matching events. |
| 4 | 🟨 | [#4 Improve origin and actor attribution](https://github.com/vince87/HA-Entity-Memory/issues/4) | Results distinguish users, automation chains and ambiguous external/device changes honestly. |
| 5 | 🟨 | [#6 Complete UI and diagnostics](https://github.com/vince87/HA-Entity-Memory/issues/6) | Setup, reconfiguration and diagnostics work without YAML. |
| 6 | ⬜ | [#5 Add CI and validation](https://github.com/vince87/HA-Entity-Memory/issues/5) | GitHub continuously validates code, Home Assistant behavior and HACS packaging. |
| 7 | ⬜ | [#7 Prepare first alpha release](https://github.com/vince87/HA-Entity-Memory/issues/7) | A documented, installable prerelease is available for controlled testing. |

## Release gates

### `0.1.0-alpha.1` — development scaffold

- Repository and HACS-compatible structure.
- Initial live cache and action interfaces.
- Not intended for installation.

### `0.1.0-alpha.2` — controlled Home Assistant testing

- ✅ Recorder restoration implemented.
- ✅ Local integration icons and translations bundled.
- ✅ Controlled-test procedure documented.
- 🟨 Home Assistant setup, reload, unload and service tests passing.
- 🟨 Climate manual-override example validated on the reference container.

### `0.1.0-alpha.3` — attribution and availability hotfix

- ✅ Query actions excluded from command correlation.
- ✅ Service/entity domain matching enforced.
- ✅ Unavailable and unknown outage/recovery pairs ignored consistently.
- 🟨 Regression behavior validated on the reference container.

### `0.1.0-beta.1` — broader testing

- Diagnostics and complete documentation.
- Coverage for light, cover, climate, switch and binary_sensor.
- HACS and CI validation passing.

### `0.1.0` — first stable release

- No known data-loss or restart-consistency defects.
- Attribution limitations clearly documented.
- Positive testing on a real Home Assistant 2026.x installation.

## Working rule

When work starts or finishes, update both the relevant issue and this roadmap in
the same change. A release is created only after all exit conditions for its
gate are satisfied.
