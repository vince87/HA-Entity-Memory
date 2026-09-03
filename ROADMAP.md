# Entity Memory roadmap

This roadmap is the project status index. Detailed acceptance criteria and
discussion live in the linked GitHub issues.

Status legend: ⬜ planned · 🟨 in progress · ✅ complete · ⛔ blocked

## Current status

The controlled-test alpha now includes live capture, bounded Recorder restore,
command-to-state correlation, query actions, UI configuration, translations,
and local Home Assistant brand icons. The Recorder, config-entry, event-listener,
response-action, manifest, and local-brand APIs have been checked against the
Home Assistant Core 2026.8.3 source. Static validation passes and controlled
testing is now in progress on the reference Home Assistant Core 2026.8.3
Container installation with Python 3.14.6 and Recorder SQLite. Recorder restart,
live capture, wildcard expansion across domains, option reload, query actions,
and log checks have passed on that system. The integration remains an alpha
while CI/HACS validation and the remaining wildcard lifecycle edge cases are
completed.

## Work plan

| Phase | Status | Work item | Exit condition |
|---|---|---|---|
| 1 | 🟨 | [#1 Harden live event capture](https://github.com/vince87/HA-Entity-Memory/issues/1) | Supported domains produce deduplicated, meaningful events with tests. |
| 2 | 🟨 | [#2 Implement Recorder restoration](https://github.com/vince87/HA-Entity-Memory/issues/2) | The 12-hour cache survives restarts with the best attribution Recorder can provide. |
| 3 | 🟨 | [#3 Finalize query actions](https://github.com/vince87/HA-Entity-Memory/issues/3) | Automations can reliably query, find and count matching events. |
| 4 | 🟨 | [#4 Improve origin and actor attribution](https://github.com/vince87/HA-Entity-Memory/issues/4) | Results distinguish users, automation chains and ambiguous external/device changes honestly. |
| 5 | 🟨 | [#6 Complete UI and diagnostics](https://github.com/vince87/HA-Entity-Memory/issues/6) | Setup, reconfiguration and diagnostics work without YAML. |
| 6 | 🟨 | [#5 Add CI and validation](https://github.com/vince87/HA-Entity-Memory/issues/5) | GitHub continuously validates code, Home Assistant behavior and HACS packaging. |
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

### `0.1.0-alpha.4` — integration placement hotfix

- ✅ Classified as an integration service instead of a helper.
- 🟨 Placement and upgrade validated on the reference container.

### `0.1.0-alpha.5` — climate automation and HACS README hotfix

- ✅ Climate `hvac_mode` no longer requires a duplicate state attribute.
- ✅ README header image uses an absolute GitHub URL for HACS rendering.
- ✅ Installation and integration placement validated on the reference container.
- ✅ Local integration icon validated in Home Assistant.
- ✅ Climate dashboard commands correlate as `authenticated_command`.
- ✅ Climate automation commands with usable parent context correlate as
  `automation`.
- ✅ Climate changes without a service call remain
  `external_or_physical` rather than being tied to a vendor integration.
- ✅ Light commands validated for dashboard/Alexa attribution and automation
  correlation, including `light.toggle`.
- ✅ Physical binary-sensor opening and closing validated as
  `device_observation`.
- ⚠️ Alexa and dashboard may share the same Home Assistant `user_id`; they are
  intentionally not distinguished without reliable source metadata. This is
  consistent with Alexa bridges that authenticate through a long-lived token
  belonging to the same Home Assistant user; a dedicated bridge user could
  provide separation, but Entity Memory remains vendor-independent.
- ✅ Implemented exact-context recovery for the observed climate automation
  case in which the service call lacks both `parent_id` and `user_id`.

### `0.1.0-alpha.6` — compact selection and automation context recovery

- ✅ Replace long entity-only configuration with combined individual selection
  and wildcard patterns.
- ✅ Cross-check `automation_triggered` by exact context ID when a matching
  service call lacks both `parent_id` and `user_id`.
- ✅ Refuse timing-only attribution so nearby or concurrent automation runs do
  not create false positives.
- 🟨 Validate wildcard setup and recovered climate automation attribution on
  the reference container.

### Remaining controlled tests and corrections

- ✅ `0.1.0-alpha.7`: ignore live startup registrations with
  `old_state: null`, clear synthetic Recorder context IDs, and revalidate
  binary-sensor restoration against Home Assistant History.
- ✅ `0.1.0-alpha.8`: resolve wildcard patterns from the entity registry during
  startup, automatically follow registry membership changes, and remove the
  hard 50-entity limit.
- ✅ Hide the default branch from HACS so testers update between named
  prereleases instead of raw commit builds.
- ✅ Validate switch commands from dashboard, automation, and a physical source
  where available.
- ✅ Validate cover open, close, and position changes from dashboard,
  automation, and a physical source where available.
- ✅ Restart Home Assistant and verify bounded restoration from Recorder SQLite.
- ✅ Verify restored events without sufficient context remain `unknown` with
  low confidence.
- ✅ Exercise `get_events`, `last_event`, `was_changed`, and `count_events`,
  including entity, state, origin, time-window, and limit filters.
- 🟨 Validate entity addition/removal, option changes, reload/unload, wildcard
  startup expansion, and rejection of unsupported domains. Option changes,
  startup expansion, multiple matching entities, and multiple domains pass;
  registry create/rename/remove remains to be exercised.
- 🟨 Confirm unavailable/recovery filtering and inspect the Home Assistant log
  after startup, reload, and shutdown. Logs are clean after update, restart,
  wildcard tests, and query-action tests; explicit unavailable/recovery testing
  remains.
- ⬜ Provide the repository icon through the mechanism expected by HACS; the
  bundled `brand/` files cover Home Assistant's integration screens but do not
  supply the HACS catalog icon.

### `0.1.0-beta.1` — broader testing

- Diagnostics and complete documentation.
- A vendor-independent example automation that consults the last remembered
  climate event before deciding whether to start cooling.
- An AI-oriented automation guide documenting action responses, defensive
  templates, attribution limits, and conservative decision rules.
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

Every build offered as an update through HACS must receive a new prerelease
version (`0.1.0-alpha.7`, `0.1.0-alpha.8`, and so on). Before publication, keep
the version in `custom_components/entity_memory/manifest.json`, the Git tag, and
the GitHub prerelease name identical. Never ask testers to update to a different
commit while retaining the previous visible version.

