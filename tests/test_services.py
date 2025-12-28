from unittest.mock import Mock, call

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
import pytest

import aiohuesyncbox
from custom_components import huesyncbox
from custom_components.huesyncbox.services import async_register_services

from .conftest import setup_integration


async def test_register_service_can_be_called_multiple_times(
    hass: HomeAssistant, mock_api: Mock
) -> None:
    await setup_integration(hass, mock_api)
    await async_register_services(hass)


async def test_set_bridge(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")}
    )
    assert device_entry is not None

    await hass.services.async_call(
        huesyncbox.DOMAIN,
        "set_bridge",
        {
            "device_id": device_entry.id,
            "bridge_id": "001788FFFE000000",
            "bridge_username": "bridge_username_value",
            "bridge_clientkey": "00112233445566778899AABBCCDDEEFF",
        },
        blocking=True,
    )
    assert mock_api.hue.set_bridge.call_count == 1
    assert mock_api.hue.set_bridge.call_args == call(
        "001788FFFE000000", "bridge_username_value", "00112233445566778899AABBCCDDEEFF"
    )


async def test_set_bridge_unknown_device_id(
    hass: HomeAssistant, mock_api: Mock
) -> None:
    await setup_integration(hass, mock_api)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            huesyncbox.DOMAIN,
            "set_bridge",
            {
                "device_id": "unknown_device_id",
                "bridge_id": "001788FFFE000000",
                "bridge_username": "bridge_username_value",
                "bridge_clientkey": "00112233445566778899AABBCCDDEEFF",
            },
            blocking=True,
        )


async def test_set_sync_state(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")}
    )
    assert device_entry is not None

    await hass.services.async_call(
        huesyncbox.DOMAIN,
        "set_sync_state",
        {
            "device_id": device_entry.id,
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


async def test_set_sync_state_no_data(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")}
    )
    assert device_entry is not None

    # The box will give back an error when setting nothing
    mock_api.execution.set_state.side_effect = aiohuesyncbox.RequestError(
        "13: Invalid Key"
    )
    await hass.services.async_call(
        huesyncbox.DOMAIN,
        "set_sync_state",
        {
            "device_id": device_entry.id,
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


async def test_set_sync_state_exception(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")}
    )
    assert device_entry is not None

    # Make sure other exceptions are not eaten by empty message logic
    mock_api.execution.set_state.side_effect = aiohuesyncbox.RequestError("Other")

    with pytest.raises(aiohuesyncbox.RequestError):
        await hass.services.async_call(
            huesyncbox.DOMAIN,
            "set_sync_state",
            {
                "device_id": device_entry.id,
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


async def test_set_sync_state_retry_on_invalid_state_streaming(
    hass: HomeAssistant,
    mock_api: Mock,
) -> None:
    mock_api.hue.groups[1]._raw["active"] = True  # noqa: SLF001
    await setup_integration(hass, mock_api)

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_device(
        identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")}
    )
    assert device_entry is not None

    mock_api.execution.set_state.side_effect = [aiohuesyncbox.InvalidState, None]
    await hass.services.async_call(
        huesyncbox.DOMAIN,
        "set_sync_state",
        {
            "device_id": device_entry.id,
        },
        blocking=True,
    )

    assert mock_api.hue.set_group_active.call_args == call("id2", active=False)
    assert mock_api.execution.set_state.call_count == 2


async def test_set_sync_state_device_id_unknown(
    hass: HomeAssistant, mock_api: Mock
) -> None:
    await setup_integration(hass, mock_api)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            huesyncbox.DOMAIN,
            "set_sync_state",
            {
                "device_id": "unknown_device_id",
            },
            blocking=True,
        )
