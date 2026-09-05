# Entity Memory roadmap

This file lists unfinished work only. Completed changes belong in release notes,
pull requests, and Git history.

## Current baseline

The current prerelease is `0.2.0-beta.2` for Home Assistant 2026.x. Entity
Memory already provides Recorder-backed event memory, live capture, conservative
origin attribution, UI and wildcard entity selection, automation query actions,
persistent registers with optimistic concurrency, privacy-safe diagnostics, and
HACS installation.

Supported entity domains are `light`, `cover`, `climate`, `switch`, and
`binary_sensor`. CI covers Python 3.14, Home Assistant 2026.8.3, Ruff, pytest,
Hassfest, and HACS validation.

## Now — complete real-installation validation

Tracked in [#19](https://github.com/vince87/HA-Entity-Memory/issues/19).
Automated coverage already exercises wildcard membership changes, all supported
domains, significant attributes, and symmetric outage/recovery filtering. The
remaining checks require a real Home Assistant installation.

- Verify wildcard selections after an entity is created, renamed, and removed.
- Verify configured handling of `unknown` and `unavailable`, including recovery
  to a valid state.
- Exercise invalid register keys and JSON values, oversized values, and the
  register-count limit; existing data must remain intact after every rejection.
- Verify an options change reloads the integration without losing event memory
  or persistent registers.
- Test a clean HACS installation of `0.2.0-beta.2` in addition to the verified
  upgrade installation.
- Run a multi-day real-automation soak test combining event queries, origin
  attribution, and persistent registers; startup, reload, runtime, and shutdown
  logs must remain clean.

Completion gate: every scenario passes on the reference installation or has a
small reproducible issue describing the failure.

## Next — freeze attribution

- Complete the real attribution matrix tracked in
  [#4](https://github.com/vince87/HA-Entity-Memory/issues/4).
- Keep ambiguous physical and external changes explicitly uncertain.
- Freeze action names, input validation, response fields, timestamp format, and
  documented error behavior for the first stable release.

Completion gate: every open issue represents unfinished work, and automation
authors can rely on one documented, tested contract.

## Next prerelease

Create another beta only when validation or contract work produces a meaningful
change.

- Resolve the HACS catalog icon delivery gap tracked in
  [#17](https://github.com/vince87/HA-Entity-Memory/issues/17).
- Keep `manifest.json`, Git tag, GitHub prerelease, and release notes on the same
  version.
- Repeat HACS clean-install and upgrade checks for the release candidate.

Completion gate: the named prerelease installs through HACS, passes all CI, and
reproduces the reference-installation results.

## First stable release

Tracked in [#18](https://github.com/vince87/HA-Entity-Memory/issues/18) and
gated by [`docs/STABLE_RELEASE_CHECKLIST.md`](docs/STABLE_RELEASE_CHECKLIST.md).

- Complete the multi-day soak test with no unresolved data-loss, corruption,
  restart-consistency, privacy, or attribution defects.
- Publish final limitations, migration notes, rollback instructions, and tested
  automation examples.
- Verify clean installation and upgrade from the latest beta on a supported
  Home Assistant 2026.x release.

Completion gate: the public API is frozen, known attribution limits are clear,
and no known defect can lose, corrupt, misattribute, or expose stored data.

## Later candidates

These are intentionally outside the first stable release unless testing proves
they are necessary:

- optional register-change events;
- configurable register-count and value-size limits;
- additional entity domains with explicit significance profiles;
- maintenance actions for bulk namespace cleanup.

## Working rules

- Keep completed work out of this file.
- Update the relevant issue and roadmap together when scope changes.
- Normally develop changes on dedicated branches and merge reviewed pull
  requests; direct commits require an explicit maintainer decision.
- Never publish an unversioned default-branch build as a HACS update.
- Keep manifest version, Git tag, GitHub release, and release notes identical.
