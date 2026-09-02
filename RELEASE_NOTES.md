# 0.1.0-alpha.4

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
