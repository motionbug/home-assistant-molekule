"""Configuration UI regressions against current Home Assistant flow classes."""

from unittest.mock import AsyncMock

import pytest
from homeassistant import loader

from custom_components.molekule import config_flow
from custom_components.molekule.api import AuthenticationError


def options_flow(hass, entry):
    flow = config_flow.MolekuleConfigFlow.async_get_options_flow(entry)
    flow.hass = hass
    flow.handler = entry.entry_id
    return flow


async def test_options_flow_uses_framework_owned_entry(hass, entry_factory):
    flow = options_flow(hass, entry_factory({"conf_refresh_rate": 123}))
    result = await flow.async_step_init()
    assert result["type"] == "form"
    fields = {key.schema: key for key in result["data_schema"].schema}
    assert fields["conf_refresh_rate"].default() == 123


async def test_options_flow_accepts_legacy_poll_interval(hass, entry_factory):
    flow = options_flow(hass, entry_factory({"sync_interval": 90}))
    result = await flow.async_step_init()
    values = result["data_schema"]({})
    assert values["conf_refresh_rate"] == 90


@pytest.mark.parametrize("interval", [0, -1])
async def test_options_schema_rejects_nonpositive_intervals(hass, entry_factory, interval):
    import voluptuous as vol
    flow = options_flow(hass, entry_factory())
    result = await flow.async_step_init()
    with pytest.raises(vol.Invalid):
        result["data_schema"]({"conf_refresh_rate": interval})


async def test_failed_authentication_closes_validation_client(hass, monkeypatch):
    api = AsyncMock()
    api.authenticate.side_effect = AuthenticationError("incorrect password")
    monkeypatch.setattr(config_flow, "MolekuleApi", lambda *args: api)
    flow = config_flow.MolekuleConfigFlow()
    flow.hass = hass
    result = await flow.async_step_user({"email": "test@example.com", "password": "bad"})
    assert result["errors"] == {"base": "invalid_auth"}
    api.close.assert_awaited_once()


@pytest.fixture
def api(monkeypatch):
    client = AsyncMock()
    client.get_devices.return_value = {"content": []}
    monkeypatch.setattr(config_flow, "MolekuleApi", lambda *args: client)
    return client


async def test_user_flow_creates_entry_after_validation(hass, api):
    flow = config_flow.MolekuleConfigFlow()
    flow.hass = hass
    flow.flow_id = "test-flow"
    flow.context = {"source": "user"}
    result = await flow.async_step_user({"email": "new@example.com", "password": "good"})
    assert result["type"] == "create_entry"
    assert result["data"] == {"email": "new@example.com", "password": "good"}
    api.close.assert_awaited_once()


async def test_reauth_updates_existing_entry(hass, entry_factory, api, monkeypatch):
    entry = entry_factory()
    flow = config_flow.MolekuleConfigFlow()
    flow.hass = hass
    flow.flow_id = "test-flow"
    flow.context = {"source": "reauth", "entry_id": entry.entry_id, "unique_id": entry.unique_id}
    reload_entry = AsyncMock(return_value=True)
    monkeypatch.setattr(hass.config_entries, "async_reload", reload_entry)
    form = await flow.async_step_reauth(entry.data)
    assert form["step_id"] == "reauth_confirm"
    result = await flow.async_step_reauth_confirm({"password": "new-password"})
    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
    assert entry.data == {"email": "test@example.com", "password": "new-password"}
    await hass.async_block_till_done()
    reload_entry.assert_awaited_once_with(entry.entry_id)
    api.close.assert_awaited_once()


async def test_options_manager_saves_options_and_reloads(hass, entry_factory, monkeypatch):
    """Exercise actual flow-manager persistence and OptionsFlowWithReload wiring."""
    entry = entry_factory({"sync_interval": 90})
    hass.data[loader.DATA_COMPONENTS]["molekule.config_flow"] = config_flow
    reload_entry = AsyncMock(return_value=True)
    monkeypatch.setattr(hass.config_entries, "async_reload", reload_entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"conf_refresh_rate": 60, "conf_silent_auto": True}
    )
    assert result["type"] == "create_entry"
    assert entry.options == {"conf_refresh_rate": 60, "conf_silent_auto": True}
    await hass.async_block_till_done()
    reload_entry.assert_awaited_once_with(entry.entry_id)
