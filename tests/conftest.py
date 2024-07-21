"""Common fixtures  for the Philips Hue Play HDMI Sync Box integration tests."""

from dataclasses import dataclass
from typing import Type
from typing_extensions import Generator

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

# Copied from HA tests/components/conftest.py
@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Test fixture that ensures all entities are enabled in the registry."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
    ):
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
    mock_api.hdmi.content_specs = "1920 x 1080 @ 60 - SDR"

    mock_api.hue = Mock(aiohuesyncbox.hue.Hue)
    mock_api.hue.bridge_unique_id = "bridge_id"
    mock_api.hue.connection_state = "connected"
    mock_api.hue.groups = [
        aiohuesyncbox.hue.Group(
            "id1", {"name": "Name 1", "numLights": 1, "active": False}
        ),
        aiohuesyncbox.hue.Group(
            "id2", {"name": "Name 2", "numLights": 2, "active": False}
        ),
    ]

    mock_api.behavior = Mock(aiohuesyncbox.behavior.Behavior)
    mock_api.behavior.force_dovi_native = 1

    return mock_api


@dataclass
class Integration:
    entry: MockConfigEntry
    mock_api: Type[Mock]


async def setup_integration(
    hass: HomeAssistant,
    mock_api,
    mock_config_entry: MockConfigEntry | None = None,
    entry_id="entry_id",
):

    entry = mock_config_entry or MockConfigEntry(
        version=2,
        minor_version=2,
        domain=huesyncbox.DOMAIN,
        entry_id=entry_id,
        unique_id="unique_id",
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host_value",
            CONF_UNIQUE_ID: "unique_id_value",
            CONF_PORT: 1234,
            CONF_PATH: "/path_value",
            CONF_ACCESS_TOKEN: "token_value",
            huesyncbox.const.REGISTRATION_ID: "registration_id_value",
        },
    )
    entry.add_to_hass(hass)

    with patch("aiohuesyncbox.HueSyncBox", return_value=mock_api):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return Integration(entry, mock_api)


async def force_coordinator_update(hass: HomeAssistant):
    async_fire_time_changed(
        hass, dt_util.utcnow() + huesyncbox.const.COORDINATOR_UPDATE_INTERVAL
    )
    await hass.async_block_till_done()
