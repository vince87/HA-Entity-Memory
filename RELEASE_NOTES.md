# 0.2.0-beta.1

Second beta for controlled Home Assistant and HACS testing.

- Added entity-less persistent registers for small automation state, with get,
  set, compare, delete, and filtered-list response actions.
- Added per-key revisions and optional optimistic concurrency through
  `expected_revision`; stale writers return a conflict without changing data.
- Added strict revision validation and separate public schemas for set and
  compare actions.
- Hardened restoration so malformed records are ignored individually while
  valid records remain available.
- Preserve the last committed in-memory value when a storage save or delete
  fails.
- Added service-contract, concurrent-writer, failed-storage, restoration, and
  schema regression tests.
- Expanded translations to English, Italian, German, French, Spanish, and
  Portuguese, and reorganized the documentation as an operational manual.
- Declared the integration as config-entry-only for YAML validation.

# 0.1.0-beta.1

First beta for broader controlled testing.

- Added continuous validation with Ruff and pytest on Python 3.14.6 and Home
  Assistant Core 2026.8.3, plus Hassfest and HACS validation.
- Added a vendor-independent climate automation example that respects a recent
  non-automation shutdown before deciding whether to restart cooling.
- Added an AI-oriented automation guide covering the four response actions,
  defensive templates, attribution limits, and conservative decision rules.
- Validated Recorder restoration, live capture, wildcard selection, query
  actions, and light, switch, cover, climate, and binary-sensor behavior on the
  reference Home Assistant container.

## Included from 0.1.0-alpha.8

- Wildcard expansion now uses the Home Assistant entity registry as well as
  currently loaded states, so patterns such as `light.*` work immediately after
  a full Home Assistant restart.
- Entity registry additions, removals, and entity-ID changes automatically
  reload wildcard selections when their resolved set changes.
- Removed the hard 50-entity limit. Broad wildcard patterns remain the user's
  choice and are documented as potentially increasing memory and Recorder load.
- Valid wildcard patterns may be saved before they have a current match.

# 0.1.0-alpha.7

- Startup state registration (`old_state: null`) is no longer stored as a real
  device observation.
- Recorder-restored events no longer expose a synthetic context ID when the
  original historical context is unavailable.
- Added regression assertions for privacy-safe restored context metadata,
  including binary sensors.
- HACS now hides the default branch and offers only named releases, so update
  dialogs display semantic versions instead of abbreviated commit SHAs.

# 0.1.0-alpha.6

- Added compact wildcard entity selection alongside the existing entity picker.
- Patterns such as `light.*`, `switch.kitchen_*`, and
  `binary_sensor.*_window` are accepted one per line or comma separated.
- Explicit selections and wildcard matches are deduplicated; the 50-entity
  safety limit applies to the resolved set.
- Existing configuration entries remain compatible and require no migration.
- Automation runs are tracked through Home Assistant's public
  `automation_triggered` event. A service call with missing parent/user metadata
  is now attributed to an automation only when it carries the exact automation
  run context; temporal proximity alone is never treated as proof.

# 0.1.0-alpha.5

Corrective prerelease for controlled testing on Home Assistant 2026.x.

## Fixed

- Entity Memory query actions no longer create false command intents for the
  entities they query.
- Command correlation now requires the service domain to match the target
  entity domain.
- When unavailable/unknown states are ignored, both the outage and the recovery
  transition are excluded from live capture and Recorder restoration.
- Entity Memory is classified as an integration service instead of a helper,
  so it is managed from the normal Integrations area.
- Climate calls carrying `hvac_mode` now compare it only with the entity state,
  allowing automation-driven temperature changes to correlate correctly.
- The README header image uses an absolute URL so it renders inside HACS.

## Included

- UI setup for up to 50 entities and a configurable rolling window.
- Live tracking for light, cover, climate, switch, and binary sensor entities.
- Significant climate, light, and cover attribute changes.
- Recorder-backed memory restoration after restart.
- Correlation between Home Assistant service calls and delayed device updates.
- Honest origin categories with a confidence level.
- Four response actions for use in automations.
- Italian and English translations.
- Transparent local brand icons for the Home Assistant integration screens.

## Known limitations

- Dashboard and Alexa commands can share the same Home Assistant user context;
  these are both reported as `authenticated_command`.
- A physical remote and an unobserved external integration can be
  indistinguishable; these are reported as `external_or_physical`.
- Recorder-restored events may have `unknown` origin with low confidence.
- This alpha still requires validation on the reference HA 2026.8.3 container.
