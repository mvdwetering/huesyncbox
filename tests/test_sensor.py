
from typing import TYPE_CHECKING

import pytest

import aiohuesyncbox

from .conftest import force_coordinator_update, setup_integration

if TYPE_CHECKING:
    from unittest.mock import Mock

    from homeassistant.core import HomeAssistant


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensor(hass: HomeAssistant, mock_api: Mock) -> None:
    """Test the total count of sensor entities after integration setup."""
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("sensor") == 9


async def test_sensor_default_disabled(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("sensor") == 4


async def test_hdmi_status(hass: HomeAssistant, mock_api: Mock) -> None:
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
async def test_ip_address(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_ip_address")
    assert entity is not None
    assert entity.state == "1.2.3.4"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_id(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_id")
    assert entity is not None
    assert entity.state == "bridge_id"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_bridge_connection_state(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_bridge_connection")
    assert entity is not None
    assert entity.state == "connected"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_entities_are_added_or_removed_when_operating_mode_changes(
    hass: HomeAssistant, mock_api: Mock
) -> None:
    bridge_entities = ("sensor.name_bridge_id", "sensor.name_bridge_connection")
    mock_api.hue.operating_mode = aiohuesyncbox.OperatingMode.BRIDGE
    next_operating_mode = aiohuesyncbox.OperatingMode.STANDALONE

    async def refresh_data() -> None:
        mock_api.hue.operating_mode = next_operating_mode

    mock_api.refresh_data.side_effect = refresh_data

    await setup_integration(hass, mock_api)
    assert all(hass.states.get(entity_id) is not None for entity_id in bridge_entities)

    await force_coordinator_update(hass)
    assert all(hass.states.get(entity_id) is None for entity_id in bridge_entities)

    next_operating_mode = aiohuesyncbox.OperatingMode.BRIDGE
    await force_coordinator_update(hass)
    assert all(hass.states.get(entity_id) is not None for entity_id in bridge_entities)


async def test_wifi_strength_not_supported(hass: HomeAssistant, mock_api: Mock) -> None:
    mock_api.device.wifi = None
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_strength")
    assert entity is None


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_wifi_strength(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_wifi_quality")
    assert entity is not None
    assert entity.state == "fair"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_content_info(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    entity = hass.states.get("sensor.name_content_info")
    assert entity is not None
    assert entity.state == "1920 x 1080 @ 60 - SDR"
