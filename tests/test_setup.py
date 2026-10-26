"""Setup failures must preserve retry/authentication semantics and close clients."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components import molekule
from custom_components.molekule.api import AuthenticationError


@pytest.fixture
def client(monkeypatch):
    api = AsyncMock()
    api.get_devices.return_value = {"content": []}
    monkeypatch.setattr(molekule, "MolekuleApi", lambda *args: api)
    return api


@pytest.mark.parametrize("failure", [None, RuntimeError("cloud unavailable")])
async def test_initial_poll_failure_closes_client(hass, entry_factory, client, failure):
    if failure is None:
        client.get_devices.return_value = None
    else:
        client.get_devices.side_effect = failure
    entry = entry_factory()
    with pytest.raises(ConfigEntryNotReady):
        await molekule.async_setup_entry(hass, entry)
    client.close.assert_awaited_once()
    assert entry.entry_id not in hass.data["molekule"]


async def test_invalid_credentials_trigger_reauthentication(hass, entry_factory, client):
    client.authenticate.side_effect = AuthenticationError("invalid credentials")
    with pytest.raises(ConfigEntryAuthFailed):
        await molekule.async_setup_entry(hass, entry_factory())
    client.close.assert_awaited_once()


async def test_cancelled_initial_poll_closes_client(hass, entry_factory, client):
    client.get_devices.side_effect = asyncio.CancelledError
    # The real coordinator converts cancellation to ConfigEntryNotReady.
    with pytest.raises(ConfigEntryNotReady):
        await molekule.async_setup_entry(hass, entry_factory())
    client.close.assert_awaited_once()


@pytest.mark.parametrize("options", [{"conf_refresh_rate": 120}, {"sync_interval": 120}])
async def test_setup_binds_entry_and_preserves_poll_interval(
    hass, entry_factory, client, monkeypatch, options
):
    entry = entry_factory(options)
    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", AsyncMock())
    assert await molekule.async_setup_entry(hass, entry)
    coordinator = hass.data["molekule"][entry.entry_id]["coordinator"]
    assert coordinator.config_entry is entry
    assert coordinator.update_interval.total_seconds() == 120
    monkeypatch.setattr(hass.config_entries, "async_unload_platforms", AsyncMock(return_value=True))
    assert await molekule.async_unload_entry(hass, entry)
    assert entry.entry_id not in hass.data["molekule"]
    client.close.assert_awaited_once()
