# Compatibility validation for 0.1.17

Validated locally on 2026-10-26 with Home Assistant 2026.10.4.

## Confirmed defects

- The published `warrant==0.6.1` dependency chain fails to import on Python 3.14:
  `python-jose-cryptodome` imports `Mapping` from `collections`.
- This fork has no GitHub releases, while its previous HACS metadata hid the
  default branch. The update allows default-branch downloads.
- The old options flow writes the removed `OptionsFlow.config_entry` setter.
- The polling form stored `sync_interval`, while setup read `conf_refresh_rate`.
- Token renewal could reacquire its own lock, and HTTP retry cleanup shut down
  the authentication executor before retrying.

## Verification

- Full regression suite: 31 tests pass, exit status 0, on Python 3.14.8 and on a
  clean Python 3.14.2 environment installed from `requirements_test.txt`.
- Tests exercise real Home Assistant flow/coordinator/entity classes, substituting
  only network responses and platform loading. Existing command URLs, payloads,
  Cognito settings and entity unique IDs are covered.
- Home Assistant 2026.10.4 hassfest: zero invalid integrations, including manifest,
  requirements declaration, configuration flow and translation validation.
- Python compilation, JSON parsing and `git diff --check` pass.
- Independent code review found no material regression. A final security test also
  verifies that authentication challenge tokens are not logged.

## Limits and follow-up

No real Molekule credentials, device or Home Assistant instance were available.
Actual HACS download/install, cloud authentication and hardware behavior require
verification after distribution. GitHub Actions have been updated but have not
run remotely; no changes have been pushed or released.

On this macOS host, running only `tests/test_config_flow.py` passes its eight
assertion tests but then crashes during Python interpreter shutdown (exit 139).
This reproduces in both Python environments; its C stack ends in module
finalization/dictionary garbage collection, and the root cause is unconfirmed.
The complete suite exits normally in both environments. The suite also emits an
upstream aiohttp/Home Assistant application-inheritance deprecation warning.

Pre-existing API behavior outside this compatibility patch: command methods may
return success after non-200 HTTP responses, and sensor/AQI helper methods suppress
authentication exceptions. Their request formats and response semantics were not
rewritten in this update.
