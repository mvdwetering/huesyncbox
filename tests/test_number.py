from unittest.mock import call

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from tests.conftest import setup_integration
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.huesyncbox.const import COORDINATOR_UPDATE_INTERVAL

async def test_number(hass: HomeAssistant, mock_api):
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("number") == 1


async def test_brightness(hass: HomeAssistant, mock_api):
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

    # # Read updated value
    # mock_api.execution.brightness = 100
    # async_fire_time_changed(
    #     hass, dt_util.utcnow() + COORDINATOR_UPDATE_INTERVAL
    # )
    # await hass.async_block_till_done()

    # brightness = hass.states.get(entity_under_test)
    # assert brightness.state == "50"
