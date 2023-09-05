from unittest.mock import call

from homeassistant.core import HomeAssistant

from .conftest import setup_integration


async def test_sensor(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("sensor") == 8


async def test_sensor_default_disabled(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api, disable_enable_default_all=True)
    assert hass.states.async_entity_ids_count("sensor") == 4


async def test_hdmi_status(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_hdmi1_status")
    assert entity is not None
    assert entity.state == "unplugged"

    entity = hass.states.get("sensor.name_hdmi2_status")
    assert entity is not None
    assert entity.state == "plugged"

    entity = hass.states.get("sensor.name_hdmi3_status")
    assert entity is not None
    assert entity.state == "linked"

    entity = hass.states.get("sensor.name_hdmi4_status")
    assert entity is not None
    assert entity.state == "unknown"


async def test_ip_address(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_ip_address")
    assert entity is not None
    assert entity.state == "1.2.3.4"


async def test_bridge_id(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_unique_id")
    assert entity is not None
    assert entity.state == "bridge_id"


async def test_bridge_connection_state(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_connection_state")
    assert entity is not None
    assert entity.state == "connected"


async def test_wifi_strength_not_supported(hass: HomeAssistant, mock_api):
    mock_api.device.wifi = None
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_strength")
    assert entity is None


async def test_wifi_strength(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_strength")
    assert entity is not None
    assert entity.state == "fair"
    assert entity.attributes["icon"] == "mdi:wifi-strength-2"
