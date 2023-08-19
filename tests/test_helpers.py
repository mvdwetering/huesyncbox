import aiohuesyncbox
import pytest
from custom_components.huesyncbox.helpers import (
    LinearRangeConverter,
    get_group_from_area_name,
)
from homeassistant.core import HomeAssistant
from unittest.mock import call

from .conftest import setup_integration


def test_linear_range_converter():
    lrc = LinearRangeConverter([-1, 1], [-11, 11])

    assert lrc.range_1_to_range_2(-1) == -11
    assert lrc.range_1_to_range_2(1) == 11
    assert lrc.range_1_to_range_2(0) == 0

    assert lrc.range_2_to_range_1(-11) == -1
    assert lrc.range_2_to_range_1(11) == 1
    assert lrc.range_2_to_range_1(0) == 0


def test_group_from_area_name(mock_api):
    assert get_group_from_area_name(mock_api, "does not exist") is None

    group = get_group_from_area_name(mock_api, "Name 1")
    assert group is not None
    assert group.id == "id1"


async def test_retry_on_invalid_state_nothing_streaming_so_no_retry(
    hass: HomeAssistant, mock_api
):
    entity_under_test = "switch.name_power"
    await setup_integration(hass, mock_api)

    entity = hass.states.get(entity_under_test)
    assert entity is not None

    mock_api.execution.set_state.side_effect = aiohuesyncbox.InvalidState
    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": entity_under_test},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(mode="powersave")
    assert mock_api.execution.set_state.call_count == 1


@pytest.mark.parametrize(
    "entity_platform, entity_under_test, service, service_data",
    [
        ("switch", "switch.name_power", "turn_off", {}),
        ("switch", "switch.name_power", "turn_on", {}),
        ("number", "number.name_brightness", "set_value", {"value": 12}),
        ("select", "select.name_sync_mode", "select_option", {"option": "video"}),
        ("huesyncbox", "switch.name_power", "set_sync_state", {"mode": "video"}),
    ],
)
async def test_retry_on_invalid_state_streaming_so_retry(
    hass: HomeAssistant,
    mock_api,
    entity_platform,
    entity_under_test,
    service,
    service_data,
):
    mock_api.hue.groups[1]._raw["active"] = True
    await setup_integration(hass, mock_api)

    entity = hass.states.get(entity_under_test)
    assert entity is not None

    mock_api.execution.set_state.side_effect = [aiohuesyncbox.InvalidState, None]
    service_data["entity_id"] = entity_under_test
    await hass.services.async_call(
        entity_platform,
        service,
        service_data,
        blocking=True,
    )
    assert mock_api.hue.set_group_active.call_args == call("id2", active=False)
    assert mock_api.execution.set_state.call_count == 2
