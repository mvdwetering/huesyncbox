from unittest.mock import call

from homeassistant.core import HomeAssistant

from tests.conftest import setup_integration


async def test_power(hass: HomeAssistant, mock_api):

    await setup_integration(hass, mock_api)

    power = hass.states.get("switch.name_power")
    assert power is not None
    assert power.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.name_power"},
        blocking=True,
    )

    assert mock_api.execution.set_state.call_args == call(mode="powersave")

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.name_power"},
        blocking=True,
    )

    assert mock_api.execution.set_state.call_args == call(mode="passthrough")
