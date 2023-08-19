from unittest.mock import call

from homeassistant.core import HomeAssistant
import pytest

from tests.conftest import setup_integration

import aiohuesyncbox

async def test_set_bridge(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "huesyncbox",
        "set_bridge",
        {
            "entity_id": "switch.name_power",  # Any entity on the device is fine
            "bridge_id": "001788FFFE000000",
            "bridge_username": "bridge_username_value",
            "bridge_clientkey": "00112233445566778899AABBCCDDEEFF",
        },
        blocking=True,
    )
    assert mock_api.hue.set_bridge.call_args == call(
        "001788FFFE000000", "bridge_username_value", "00112233445566778899AABBCCDDEEFF"
    )


async def test_set_sync_state(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    await hass.services.async_call(
        "huesyncbox",
        "set_sync_state",
        {
            "entity_id": "switch.name_power",  # Any entity on the device is fine
            "power": True,
            "sync": True,
            "brightness": 42,
            "intensity": "high",
            "mode": "video",
            "input": "input1",
            "entertainment_area": "Name 1",
        },
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(
        hdmi_active=True,
        sync_active=True,
        mode="video",
        hdmi_source="input1",
        brightness=83,
        intensity="high",
        hue_target="id1",
    )

async def test_set_sync_state_no_data(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    # The box will give back an error when setting nothing
    mock_api.execution.set_state.side_effect=aiohuesyncbox.RequestError("13: Invalid Key")
    await hass.services.async_call(
        "huesyncbox",
        "set_sync_state",
        {
            "entity_id": "switch.name_power",  # Any entity on the device is fine
        },
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(
        hdmi_active=None,
        sync_active=None,
        mode=None,
        hdmi_source=None,
        brightness=None,
        intensity=None,
        hue_target=None,
    )

async def test_set_sync_state_exception(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)

    # Make sure other exceptions are not eaten by empty message logic
    with pytest.raises(aiohuesyncbox.RequestError):
        mock_api.execution.set_state.side_effect=aiohuesyncbox.RequestError("Other")
        await hass.services.async_call(
            "huesyncbox",
            "set_sync_state",
            {
                "entity_id": "switch.name_power",  # Any entity on the device is fine
            },
            blocking=True,
        )
        assert mock_api.execution.set_state.call_args == call(
            hdmi_active=None,
            sync_active=None,
            mode=None,
            hdmi_source=None,
            brightness=None,
            intensity=None,
            hue_target=None,
        )
