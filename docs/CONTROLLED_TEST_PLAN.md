# Controlled test plan for `0.1.0-alpha.8`

Run this plan only on the reference Home Assistant 2026.8.3 Container system.
Use test entities or anonymize all IDs before sharing results publicly.

## Before installation

1. Back up `/config` and the Recorder database.
2. Confirm Home Assistant Core 2026.8.3, Python 3.14.6, HACS 2.0.5, and SQLite.
3. Record the current Home Assistant log baseline and restart duration.

## Install and configure

1. Add `vince87/HA-Entity-Memory` as a HACS custom integration repository.
2. Enable prereleases for the repository, select `0.1.0-alpha.8`, download it,
   and restart Home Assistant.
3. Confirm that **Entity Memory** appears under **Add integration** and no
   longer appears as a helper type.
4. Add one test entity from each supported domain: `light`, `cover`, `climate`,
   `switch`, and `binary_sensor`.
5. Keep the default 12-hour window, enable significant attribute changes, and
   keep unknown/unavailable states ignored.
6. Reopen the options, change the entity selection, save, and confirm that the
   entry reloads without an error. Restore the five-entity test selection.
7. Replace some individual selections with wildcard patterns such as
   `light.*` and a narrower name pattern. Confirm matching entities are tracked,
   and unrelated entities are excluded. Restart Home Assistant and verify that
   wildcard matches work without manually reloading Entity Memory.
8. Add, rename, or remove a matching test entity and confirm that wildcard
   membership updates automatically. Use broad patterns parsimoniously because
   there is no hard entity limit and Recorder work grows with the resolved set.

## Query-action smoke tests

From **Developer tools > Actions**, call all four actions with anonymized test
entity IDs and `since: "00:30:00"`:

- `entity_memory.get_events`: response contains `events` and `count`.
- `entity_memory.last_event`: response contains the newest event or `null`.
- `entity_memory.was_changed`: response contains `found` and `event`.
- `entity_memory.count_events`: response contains `count`.

Repeat with `to_state`, each `origins` value, multiple entities, and limits 1
and 1000. Confirm timestamps are ISO 8601 and results are newest first.
Calling a query action must never appear later as `matched_service`.

## Live capture and attribution

For every supported domain, create a real state change and verify that exactly
one meaningful event appears. Then verify these specific cases:

1. A dashboard or companion-app command is `authenticated_command` with high
   confidence after its resulting state change.
2. An automation command is `automation` with high confidence.
   Repeat with an automation whose resulting service call previously had no
   `parent_id`; an exact `automation_triggered` context match must still recover
   `automation`. A nearby unrelated automation must not be used.
3. An Alexa command using the same Home Assistant account as the dashboard is
   also `authenticated_command`; it must not be labeled as Alexa artificially.
4. The physical ESPHome climate remote, when it has no matching service call,
   user ID, or parent ID, is `external_or_physical` with medium confidence.
5. A binary-sensor transition without a matching command is
   `device_observation` with high confidence.
6. A matching device confirmation within 180 seconds carries `matched_service`;
   a transition after more than 180 seconds does not reuse the expired command.
7. Target-temperature, fan-mode, swing-mode, and HVAC changes are retained;
   current-temperature-only updates are not.
8. Relevant light and cover attribute changes are retained. Unrelated attribute
   changes and ignored unknown/unavailable states are not.

## Recorder restart test

1. Generate several known events and note their times without publishing IDs.
2. Restart Home Assistant inside the 12-hour window.
3. Immediately generate one additional live event during or just after startup.
4. Confirm old events are restored, the startup-boundary event is present once,
   and ordering remains newest first.
5. Confirm every restored event without reliable context is `unknown` with low
   confidence, including restored binary-sensor events.
6. Confirm events older than 12 hours and events from unconfigured entities are
   absent.
7. Review startup time and logs for Recorder query errors, event-loop blocking,
   duplicate action registration, and unexpected database warnings.

## Pass criteria and report

The alpha passes only if setup, options reload, all four actions, all five
domains, correlation, attribution fallbacks, and restart restoration behave as
above without errors. Report the Home Assistant version, installation type,
anonymized steps, expected/actual result, and relevant sanitized log lines.
