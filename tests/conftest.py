"""Common fixtures  for the Philips Hue Play HDMI Sync Box integration tests."""

from dataclasses import dataclass
from typing import Type
from unittest.mock import Mock, patch
import pytest

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
)

import aiohuesyncbox

from custom_components import huesyncbox


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""
    yield


@pytest.fixture
def mock_api(hass):
    """Create a mocked HueSyncBox instance."""
    mock_api = Mock(
        spec=aiohuesyncbox.HueSyncBox,
    )

    mock_api.device = Mock(aiohuesyncbox.device.Device)
    mock_api.device.name = "Name"
    mock_api.device.api_level = 7
    mock_api.device.device_type = "HSB1"
    mock_api.device.firmware_version = "firmwareversion"
    mock_api.device.unique_id = "unique_id"
    mock_api.device.led_mode = 1
    mock_api.device.ip_address = "1.2.3.4"

    mock_api.execution = Mock(aiohuesyncbox.execution.Execution)
    mock_api.execution.brightness = 120
    mock_api.execution.mode = "video"
    mock_api.execution.sync_active = False

    mock_api.hdmi = Mock(aiohuesyncbox.hdmi.Hdmi)
    mock_api.hdmi.input1 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input1.name = "HDMI 1"
    mock_api.hdmi.input1.type = "generic"
    mock_api.hdmi.input1.status = "unplugged"
    mock_api.hdmi.input2 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input2.name = "HDMI 2"
    mock_api.hdmi.input2.type = "generic"
    mock_api.hdmi.input2.status = "unplugged"
    mock_api.hdmi.input3 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input3.name = "HDMI 3"
    mock_api.hdmi.input3.type = "generic"
    mock_api.hdmi.input3.status = "unplugged"
    mock_api.hdmi.input4 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input4.name = "HDMI 4"
    mock_api.hdmi.input4.type = "generic"
    mock_api.hdmi.input4.status = "unplugged"

    mock_api.hue = Mock(aiohuesyncbox.hue.Hue)
    mock_api.hue.bridge_id = "bridge_id"
    mock_api.hue.connection_state = "idle"
    mock_api.hue.groups = [
        aiohuesyncbox.hue.Group(
            "id1", {"name": "Name 1", "numLights": 1, "active": False}
        )
    ]

    mock_api.behavior = Mock(aiohuesyncbox.behavior.Behavior)
    mock_api.behavior.force_dovi_native = None

    return mock_api


@dataclass
class Integration:
    entry: MockConfigEntry
    mock_api: Type[Mock]


async def setup_integration(hass, mock_api):
    entry_id = "entry_id"

    coordinator: huesyncbox.HueSyncBoxCoordinator = Mock()
    coordinator.data = mock_api

    hass.data.setdefault(huesyncbox.DOMAIN, {})
    hass.data[huesyncbox.DOMAIN][entry_id] = coordinator

    entry = MockConfigEntry(
        version=2,
        domain=huesyncbox.DOMAIN,
        entry_id=entry_id,
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host",
            CONF_UNIQUE_ID: "unique_id",
            CONF_PORT: 1234,
            CONF_PATH: "/api_path",
            CONF_ACCESS_TOKEN: "token",
            huesyncbox.const.REGISTRATION_ID: "42",
        },
    )
    entry.add_to_hass(hass)

    with patch("aiohuesyncbox.HueSyncBox", return_value=mock_api):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return Integration(entry, mock_api)
