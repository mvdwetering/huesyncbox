from homeassistant.core import HomeAssistant
import pytest

from .conftest import setup_integration


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensor(hass: HomeAssistant, mock_api):
    """Test the total count of sensor entities after integration setup."""
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("sensor") == 9


async def test_sensor_default_disabled(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)
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


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_ip_address(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_ip_address")
    assert entity is not None
    assert entity.state == "1.2.3.4"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_id(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_id")
    assert entity is not None
    assert entity.state == "bridge_id"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_connection_state(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_connection")
    assert entity is not None
    assert entity.state == "connected"


async def test_wifi_strength_not_supported(hass: HomeAssistant, mock_api):
    mock_api.device.wifi = None
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_strength")
    assert entity is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_wifi_strength(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_quality")
    assert entity is not None
    assert entity.state == "fair"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_content_info(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_content_info")
    assert entity is not None
    assert entity.state == "1920 x 1080 @ 60 - SDR"
