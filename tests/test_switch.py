from unittest.mock import call

from homeassistant.core import HomeAssistant

from .conftest import force_coordinator_update, setup_integration

async def test_switch(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("switch") == 3


async def test_power(hass: HomeAssistant, mock_api):
    entity_under_test = "switch.name_power"

    await setup_integration(hass, mock_api)

    # Value read from API
    power = hass.states.get(entity_under_test)
    assert power is not None
    assert power.state == "on"

    mock_api.execution.mode = "powersave"
    await force_coordinator_update(hass)
    power = hass.states.get(entity_under_test)
    assert power is not None
    assert power.state == "off"

    # Turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(mode="powersave")

    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(mode="passthrough")


async def test_lightsync(hass: HomeAssistant, mock_api):
    entity_under_test = "switch.name_light_sync"

    await setup_integration(hass, mock_api)

    # Value read from API
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "on"

    # Turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(sync_active=False)

    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(sync_active=True)


async def test_dolby_vision_compatibility_not_supported(hass: HomeAssistant, mock_api):
    mock_api.behavior.force_dovi_native = None
    await setup_integration(hass, mock_api)

    entity = hass.states.get("switch.name_dolby_vision_compatibility")
    assert entity is None


async def test_dolby_vision_compatibility_supported(hass: HomeAssistant, mock_api):
    entity_under_test = "switch.name_dolby_vision_compatibility"
    await setup_integration(hass, mock_api)

    # Value read from API
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "on"

    # Turn off
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.behavior.set_force_dovi_native.call_args == call(0)

    # Turn on
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.behavior.set_force_dovi_native.call_args == call(1)
