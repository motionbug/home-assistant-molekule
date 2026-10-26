# Repository Guidelines

## Project Structure & Module Organization

The integration lives in `custom_components/molekule/`. `__init__.py` manages setup, polling through a `DataUpdateCoordinator`, and unloading; `api.py` handles cloud authentication and requests. `fan.py` and `sensor.py` expose entities, `config_flow.py` defines setup and options, and `const.py` holds shared constants. Keep configuration labels in `strings.json` and integration metadata in `manifest.json`. Root-level `hacs.json` configures HACS distribution. CI workflows live in `.github/workflows/`. There are no dedicated test or asset directories.

## Build, Test, and Development Commands

There is no standalone build or development server; run this code within Home Assistant.

- `python3 -m compileall -q custom_components/molekule`: check Python syntax; this does not validate Home Assistant behavior.
- `python3 -m json.tool custom_components/molekule/manifest.json`: validate manifest JSON syntax; repeat for `strings.json` and `hacs.json` when changed.
- `git diff --check`: catch whitespace errors before submitting.

For local testing, copy `custom_components/molekule/` into a development Home Assistant instance's `config/custom_components/`, restart Home Assistant, and add Molekule through the integrations UI. CI runs hassfest and HACS integration validation on pushes and pull requests.

## Coding Style & Naming Conventions

Use four spaces for Python indentation, `snake_case` for functions and variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Follow existing asynchronous Home Assistant patterns; keep blocking authentication work off the event loop. Add type annotations and concise docstrings when extending public methods. No formatter or linter is configured; avoid unrelated formatting changes.

## Testing Guidelines

No automated test framework or coverage threshold is configured. Manually verify authentication, device discovery, sensor updates, fan mode/speed changes, options changes, and integration reload/unload as relevant. Record the device model and Home Assistant version tested; Air Pro has the strongest documented testing history. If adding automated tests, use descriptive `test_*.py` files under `tests/` and document dependencies and execution commands.

## Commit & Pull Request Guidelines

History uses short, informal commit subjects without a consistent prefix convention. Prefer concise, descriptive subjects such as `Fix fan speed updates`. Keep commits focused. PRs should describe the problem, behavior changes, validation performed, and related issues. Include screenshots for visible UI changes. For releases, keep versions in `manifest.json` and `README.md` aligned.

## Security & Configuration

Never commit account credentials, authentication tokens, or unredacted device responses. Configure credentials through the integration UI and redact sensitive fields from logs and issue reports.
