"""Pin model support, entity identities and command mappings during migration."""

from importlib import import_module
from unittest.mock import AsyncMock

from homeassistant.components.fan import FanEntityFeature

from custom_components import molekule


async def test_platform_setup_reuses_poll_and_preserves_entities(hass, entry_factory, monkeypatch):
    api = AsyncMock()
    api.get_devices.return_value = {"content": [
        {"serialNumber": "air", "name": "Bedroom", "subProduct": {"name": "Molekule Air"}},
        {"serialNumber": "pro", "name": "Office", "subProduct": {"name": "Molekule Air Pro"}},
    ]}
    api.get_sensor_data.return_value = {"PM2_5": 7, "RH": 45, "TVOC": 3, "CO2": 500, "PM10": 9}
    monkeypatch.setattr(molekule, "MolekuleApi", lambda *args: api)
    entities = {"fan": [], "sensor": []}

    async def forward(entry, platforms):
        for name in platforms:
            platform = import_module(f"custom_components.molekule.{name}")
            await platform.async_setup_entry(
                hass, entry, lambda added, *args: entities[name].extend(added)
            )

    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", forward)
    entry = entry_factory({"conf_silent_auto": True})
    assert await molekule.async_setup_entry(hass, entry)
    api.get_devices.assert_awaited_once()
    api.get_sensor_data.assert_awaited_once_with("pro")

    fans = {fan.unique_id: fan for fan in entities["fan"]}
    assert set(fans) == {"air_fan", "pro_fan"}
    assert fans["air_fan"].speed_count == 3
    assert fans["pro_fan"].speed_count == 6
    assert not fans["air_fan"].supported_features & FanEntityFeature.PRESET_MODE
    assert fans["pro_fan"].preset_modes == ["auto", "manual"]

    sensors = {sensor.unique_id: sensor for sensor in entities["sensor"]}
    assert set(sensors) == {
        "air_peco_filter", "pro_peco_filter", "pro_air_quality", "pro_Humidity",
        "pro_PM2.5", "pro_PM10", "pro_VOC", "pro_CO2",
    }
    assert sensors["pro_Humidity"].native_value == 45
    assert sensors["pro_PM2.5"].native_value == 7
    assert sensors["pro_VOC"].native_unit_of_measurement == "μg/m³"
    assert sensors["pro_CO2"].native_unit_of_measurement == "ppm"

    coordinator = hass.data["molekule"][entry.entry_id]["coordinator"]
    monkeypatch.setattr(coordinator, "async_request_refresh", AsyncMock())
    await fans["pro_fan"].async_set_preset_mode("auto")
    api.set_auto_mode.assert_awaited_once_with("pro", True, True)
    await fans["air_fan"].async_set_percentage(100)
    api.set_fan_speed.assert_awaited_once_with("air", 3)
    await api.close()
