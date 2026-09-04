# Entity Memory roadmap

This roadmap contains only planned work. Completed implementation history lives
in Git history, pull requests, and release notes.

## Current baseline

Entity Memory is an installable beta for Home Assistant 2026.x. It provides a
bounded entity-event cache restored from Recorder, live change capture, honest
origin attribution, individual and wildcard entity selection, response-data
query actions, and entity-less persistent registers for automation state.

The supported entity domains are `light`, `cover`, `climate`, `switch`, and
`binary_sensor`. CI validates Python 3.14, Home Assistant 2026.8.3, Ruff, pytest,
Hassfest, and HACS packaging.

## Priorities

### P0 — Validate the expanded beta

Goal: prove that existing event memory and the new persistent registers behave
reliably on a real Home Assistant installation.

- Exercise all register actions from Developer Tools and automations:
  `get_register`, `set_register`, `compare_register`, `delete_register`, and
  `list_registers`.
- Verify register persistence across restart, integration reload, option reload,
  and upgrade from `0.1.0-beta.1`.
- Verify no-op writes preserve `revision` and `updated_at`, while changed values
  increment the revision exactly once.
- Verify invalid keys, invalid JSON values, oversized values, and the register
  count limit fail clearly without damaging existing data.
- Exercise wildcard membership changes for entity create, rename, and removal.
- Exercise explicit `unknown`/`unavailable` outage and recovery transitions.
- Run a multi-day automation soak test combining event attribution and registers.

Related tracking: [#1](https://github.com/vince87/HA-Entity-Memory/issues/1),
[#2](https://github.com/vince87/HA-Entity-Memory/issues/2),
[#3](https://github.com/vince87/HA-Entity-Memory/issues/3), and
[#6](https://github.com/vince87/HA-Entity-Memory/issues/6).

Exit condition: all scenarios pass on the reference installation with clean
startup, reload, runtime, and shutdown logs.

### P1 — Finish attribution and query contracts

Goal: freeze the public behavior needed by automation authors before `1.0`.

- Review the remaining acceptance criteria in
  [#1](https://github.com/vince87/HA-Entity-Memory/issues/1),
  [#2](https://github.com/vince87/HA-Entity-Memory/issues/2),
  [#3](https://github.com/vince87/HA-Entity-Memory/issues/3),
  [#4](https://github.com/vince87/HA-Entity-Memory/issues/4), and
  [#6](https://github.com/vince87/HA-Entity-Memory/issues/6).
- Close completed issues and replace broad leftovers with small, testable issues.
- Keep safety interlocks explicitly outside Entity Memory's responsibility.

Exit condition: every open issue describes unfinished work, and the automation
guide matches the tested public API exactly.

### P2 — Release the next beta

Goal: publish one coherent HACS-testable build containing the remaining beta
hardening and attribution work.

- Select the next prerelease version after testing; do not expose unversioned
  default-branch builds as updates.
- Keep `manifest.json`, Git tag, GitHub prerelease name, and release notes on the
  same version.
- Document upgrade, rollback, and register cleanup procedures.
- Resolve the HACS catalog icon delivery gap.
- Test a clean installation and an upgrade from `0.1.0-beta.1`.

Exit condition: the named prerelease installs and upgrades through HACS, passes
CI, and reproduces the reference-installation results.

### P3 — First stable release

Goal: promote the tested API without known persistence or restart defects.

- Complete a multi-day real-installation soak test.
- Resolve all defects that can lose, corrupt, misattribute, or unexpectedly
  expose stored data.
- Freeze action names and response shapes for the stable release.
- Publish final user documentation, automation examples, limitations, migration
  notes, and rollback instructions.

Exit condition: no known data-loss or restart-consistency defects, attribution
limits are explicit, and both clean-install and upgrade tests pass on Home
Assistant 2026.x.

## Later candidates

These ideas are intentionally outside the first stable release unless beta
testing proves they are necessary:

- optional register-change events;
- configurable register count and value-size limits;
- additional entity domains with explicit significance profiles;
- diagnostic or maintenance actions for bulk namespace cleanup.

## Working rules

- Develop every change on a dedicated branch and merge it through a reviewed
  pull request.
- Keep completed work out of this file; record it in release notes and Git
  history instead.
- Update the relevant issue and this roadmap together when scope or priority
  changes.
- Do not publish a HACS update without a new named prerelease version.
- Keep the manifest version, Git tag, GitHub prerelease, and release notes
  identical for every published build.
