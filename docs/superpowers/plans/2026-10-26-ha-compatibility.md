# Home Assistant Compatibility Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore current Home Assistant compatibility without changing the Molekule API protocol.

**Architecture:** Retain the API client, coordinator and entity platforms. Patch dependency, setup, options and connection lifecycle boundaries, with network-isolated regression tests against real Home Assistant classes.

**Tech Stack:** Python, Home Assistant, aiohttp, Cognito SRP, pytest, pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-10-26-ha-compatibility-design.md`

## Global Constraints

- Preserve Molekule endpoints, payloads, Cognito configuration and entity unique IDs.
- No real credentials or real network calls in tests.
- Leave AGENTS.md unchanged.

## Review Focus

- Failed authentication must close the client and display an appropriate UI error.
- Failed initial polling must release resources and allow setup retry.
- Legacy polling options must remain usable after upgrade.
- Token renewal failure and request retries must permit subsequent authentication.
- Air and Air Pro entity identities and command payloads must remain stable.

## Task 1: Establish installation and API regression tests

Files: `tests/test_api.py`, `tests/conftest.py`, `requirements_test.txt`, `custom_components/molekule/api.py`, `custom_components/molekule/manifest.json`.

Interface: retain `MolekuleApi` public methods and return types.

1. Reproduce dependency installation/import problems on current Python.
2. Write tests for refresh fallback, retry authentication, and existing API URLs/payloads; run and inspect failures.
3. Replace obsolete authentication dependency if required; fix nested locking and distinguish session reset from final shutdown.
4. Run API tests and confirm command contract tests pass.

## Task 2: Update setup and UI integration

Files: `tests/test_setup.py`, `tests/test_config_flow.py`, `tests/test_entities.py`, `custom_components/molekule/{__init__,config_flow,fan,sensor}.py`, `strings.json`, `translations/en.json`.

Interface: retain config-entry account keys and all entity unique IDs; Task 1 supplies the same API client methods.

1. Write failing tests for read-only options entry, polling key/legacy values, failed authentication cleanup, failed setup cleanup and model-specific entity IDs.
2. Bind coordinator explicitly; fix exception handling and cleanup. Remove redundant first-refresh calls in platforms.
3. Update options flow and translation strings; retain existing account-update behavior.
4. Run complete tests against installed Home Assistant.

## Task 3: Distribution and verification

Files: `README.md`, `hacs.json`, `.github/workflows/`, test configuration, release manifest.

1. Document supported/tested Home Assistant and Python versions, installation, troubleshooting and test commands.
2. Pin requirements, synchronize release version, add CI regression tests alongside hassfest/HACS validation.
3. Run complete pytest suite, syntax/JSON/whitespace checks and review the final diff.
4. Obtain an independent code review and address material findings with failing regression tests before reporting results.

Execution is authorized by the user's approval. Work in a local fix branch; no release, push or merge is requested.
