from unittest.mock import Mock, call

from homeassistant.core import HomeAssistant

from .conftest import setup_integration


async def test_number(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("number") == 1


async def test_brightness(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "number.name_brightness"

    await setup_integration(hass, mock_api)

    # Initial value
    brightness = hass.states.get(entity_under_test)
    assert brightness is not None
    assert brightness.state == "60"

    # Set value
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": entity_under_test, "value": 75},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(brightness=149)
