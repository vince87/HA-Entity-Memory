# Stable release checklist

Do not publish `1.0.0` until every required item below is complete. Record real
installation evidence without publishing household identifiers.

## Automated gate

- Ruff formatting and lint pass.
- The complete pytest suite passes on the supported Python and Home Assistant
  versions.
- Hassfest and HACS validation pass.
- JSON, translations, `services.yaml`, and relative documentation links are
  valid.
- Action names, schemas, response shapes, missing-data behavior, register
  revision rules, and timestamp format match the public documentation.

## HACS distribution gate

- A clean install of the named release succeeds.
- Upgrade from `0.2.0-beta.2` preserves the config entry and registers.
- HACS and Home Assistant display the semantic version, not a commit hash.
- Integration setup, reload, restart, diagnostics download, and removal behave
  without Entity Memory errors.
- Installation, rollback, and register-cleanup instructions are verified.

## Real-installation gate

- Wildcard membership follows entity creation, rename, and removal.
- Ignored `unknown`/`unavailable` outages and recoveries behave as documented.
- Every supported domain records state transitions and only its meaningful
  attributes.
- Dashboard, automation, physical/external, and binary-sensor observations use
  conservative attribution with the documented confidence.
- Recorder restoration is bounded, deduplicated, correctly ordered, and safe
  when historical context is unavailable.
- A multi-day automation soak test completes with clean startup, reload,
  runtime, and shutdown logs.

## Privacy and recovery gate

- Diagnostics contain no entity IDs, register keys or values, user IDs, or
  context IDs.
- Invalid, oversized, conflicting, and over-limit register writes preserve
  existing data.
- A supported backup and rollback procedure has been exercised.
- There are no open defects involving data loss, corruption, privacy exposure,
  restart consistency, or false attribution certainty.

## Publication gate

- Remaining beta issues are closed or explicitly deferred.
- `manifest.json`, Git tag, GitHub release name, and release notes all use
  `1.0.0`.
- Final limitations, migration notes, automation examples, and rollback steps
  are published.
- The release is created from the exact commit that passed every gate.
