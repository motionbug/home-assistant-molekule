"""Real Home Assistant objects; only cloud and platform loading are mocked."""

from types import MappingProxyType

import pytest
from homeassistant import loader
from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import frame


@pytest.fixture
async def hass(tmp_path):
    instance = HomeAssistant(str(tmp_path))
    frame.async_setup(instance)
    loader.async_setup(instance)
    instance.config_entries = ConfigEntries(instance, {})
    await instance.config_entries.async_initialize()
    yield instance
    for entry in instance.config_entries.async_entries():
        await entry._async_process_on_unload(instance)
    await instance.async_stop(force=True)
    # Match Home Assistant's fixture cleanup: do not retain a stopped instance.
    frame.async_setup(None)


@pytest.fixture
def entry_factory(hass):
    def create(options=None):
        entry = ConfigEntry(
            domain="molekule", title="test@example.com", version=1, minor_version=1,
            data={"email": "test@example.com", "password": "test-password"},
            options=options or {}, source="user", unique_id="test@example.com",
            discovery_keys=MappingProxyType({}), subentries_data=[],
            state=ConfigEntryState.SETUP_IN_PROGRESS,
        )
        hass.config_entries._entries[entry.entry_id] = entry
        return entry
    return create
