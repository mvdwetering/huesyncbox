from unittest.mock import call

from homeassistant.core import HomeAssistant

from tests.conftest import setup_integration


async def test_brightness(hass: HomeAssistant, mock_api):

    await setup_integration(hass, mock_api)

    brightness = hass.states.get("number.name_brightness")
    assert brightness is not None
    assert brightness.state == "60"

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.name_brightness", "value": 75},
        blocking=True,
    )

    assert mock_api.execution.set_state.call_args == call(brightness=149)
