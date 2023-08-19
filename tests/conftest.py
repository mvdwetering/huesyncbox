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
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.util import dt as dt_util

from pytest_homeassistant_custom_component.common import async_fire_time_changed
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
    mock_api.device.wifi = Mock(aiohuesyncbox.device.Wifi)
    mock_api.device.wifi.strength = 2

    mock_api.execution = Mock(aiohuesyncbox.execution.Execution)
    mock_api.execution.brightness = 120
    mock_api.execution.mode = "music"
    mock_api.execution.last_sync_mode = "game"
    mock_api.execution.sync_active = False
    mock_api.execution.hdmi_source = "input2"
    mock_api.execution.hue_target = "id2"
    mock_api.execution.video = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.video.intensity = "subtle"
    mock_api.execution.music = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.music.intensity = "moderate"
    mock_api.execution.game = Mock(aiohuesyncbox.execution.SyncMode)
    mock_api.execution.game.intensity = "intense"

    mock_api.hdmi = Mock(aiohuesyncbox.hdmi.Hdmi)
    mock_api.hdmi.input1 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input1.name = "HDMI 1"
    mock_api.hdmi.input1.type = "generic"
    mock_api.hdmi.input1.status = "unplugged"
    mock_api.hdmi.input2 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input2.name = "HDMI 2"
    mock_api.hdmi.input2.type = "generic"
    mock_api.hdmi.input2.status = "plugged"
    mock_api.hdmi.input3 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input3.name = "HDMI 3"
    mock_api.hdmi.input3.type = "generic"
    mock_api.hdmi.input3.status = "linked"
    mock_api.hdmi.input4 = Mock(aiohuesyncbox.hdmi.Input)
    mock_api.hdmi.input4.name = "HDMI 4"
    mock_api.hdmi.input4.type = "generic"
    mock_api.hdmi.input4.status = "unknown"

    mock_api.hue = Mock(aiohuesyncbox.hue.Hue)
    mock_api.hue.bridge_unique_id = "bridge_id"
    mock_api.hue.connection_state = "connected"
    mock_api.hue.groups = [
        aiohuesyncbox.hue.Group(
            "id1", {"name": "Name 1", "numLights": 1, "active": False}
        ),
        aiohuesyncbox.hue.Group(
            "id2", {"name": "Name 2", "numLights": 2, "active": False}
        )
    ]

    mock_api.behavior = Mock(aiohuesyncbox.behavior.Behavior)
    mock_api.behavior.force_dovi_native = 1

    return mock_api


@dataclass
class Integration:
    entry: MockConfigEntry
    mock_api: Type[Mock]


async def setup_integration(hass:HomeAssistant, mock_api, disable_enable_default_all=False):
    entry_id = "entry_id"

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

    if not disable_enable_default_all:
        # Pre-create registry entries for default disabled ones
        er = entity_registry.async_get(hass)
        for default_disabled_sensor in ["ip_address", "wifi_strength", "bridge_unique_id", "bridge_connection_state"]:
            er.async_get_or_create(
                "sensor",
                huesyncbox.DOMAIN,
                f"{default_disabled_sensor}_unique_id",
                suggested_object_id=f"name_{default_disabled_sensor}",
                disabled_by=None,
            )

    with patch("aiohuesyncbox.HueSyncBox", return_value=mock_api):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return Integration(entry, mock_api)

async def force_coordinator_update(hass:HomeAssistant):
    async_fire_time_changed(
        hass, dt_util.utcnow() + huesyncbox.const.COORDINATOR_UPDATE_INTERVAL
    )
    await hass.async_block_till_done()
