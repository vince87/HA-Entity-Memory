# Reference Home Assistant environment

This is the first real installation targeted during development. It contains
no credentials or network identifiers.

| Component | Value |
|---|---|
| Home Assistant Core | `2026.8.3` |
| Installation | Home Assistant Container |
| Container architecture | `amd64` |
| Host OS family | Linux |
| CPU architecture | `x86_64` |
| Python | `3.14.6` |
| Time zone | `Europe/Rome` |
| Configuration directory | `/config` |
| Supervisor | No |
| HACS | `2.0.5` |
| Recorder engine | SQLite |
| SQLite | `3.53.2` |
| Recorder database size | Approximately `2368.74 MiB` |
| Oldest observed Recorder run | 2026-08-16 20:06 local time |

## Design consequences

- SQLite is the first database used for integration testing, while Recorder
  access must remain portable to other Home Assistant-supported databases.
- Restoration queries must be bounded by configured entity IDs and the rolling
  time window; full database scans are unacceptable.
- Database work must run through Home Assistant's Recorder facilities and must
  not block the event loop.
- Timestamps must remain timezone-aware. Service responses use ISO 8601, while
  internal comparisons use UTC.
- The integration must work without Supervisor and must not depend on add-ons.
- Python 3.14 is the primary runtime target for the reference installation.

## Still needed before integration testing

- Representative entity states and attributes for each selected domain.
- The climate automation YAML used for the first manual-override scenario.
- Sample `state_changed` events for dashboard, automation, physical control,
  and vendor-app actions where available.

