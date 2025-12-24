from unittest.mock import Mock, call

from homeassistant.core import HomeAssistant

from .conftest import force_coordinator_update, setup_integration


async def test_select(hass: HomeAssistant, mock_api: Mock) -> None:
    await setup_integration(hass, mock_api)
    assert hass.states.async_entity_ids_count("select") == 5


async def test_input(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_hdmi_input"

    await setup_integration(hass, mock_api)

    # Initial value
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "HDMI 2"
    assert entity.attributes["options"] == ["HDMI 1", "HDMI 2", "HDMI 3", "HDMI 4"]

    # Set value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_under_test, "option": "HDMI 3"},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(hdmi_source="input3")


async def test_input_unsupported_value(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_hdmi_input"
    mock_api.execution.hdmi_source = "invalid_input"

    await setup_integration(hass, mock_api)

    # Initial value
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "unknown"  # HA seems to map unsupported values to "unknown"


async def test_intensity(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_intensity"

    await setup_integration(hass, mock_api)

    # Initial value
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "moderate"
    assert entity.attributes["options"] == ["subtle", "moderate", "high", "intense"]

    # Set value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_under_test, "option": "high"},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(music={"intensity": "high"})


async def test_mode(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_sync_mode"

    await setup_integration(hass, mock_api)

    # Value when box is syncing
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "music"
    assert entity.attributes["options"] == ["video", "music", "game"]

    # Value when box is not syncing uses last_sync_mode
    mock_api.execution.mode = "passthrough"
    await force_coordinator_update(hass)

    entity = hass.states.get(entity_under_test)
    assert entity.state == "game"

    # Set value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_under_test, "option": "video"},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(mode="video")


async def test_entertainment_area(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_entertainment_area"

    await setup_integration(hass, mock_api)

    # Initial value
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "Name 2"
    assert entity.attributes["options"] == ["Name 1", "Name 2"]

    # Set value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_under_test, "option": "Name 1"},
        blocking=True,
    )
    assert mock_api.execution.set_state.call_args == call(hue_target="id1")


async def test_led_indicator(hass: HomeAssistant, mock_api: Mock) -> None:
    entity_under_test = "select.name_led_indicator"

    await setup_integration(hass, mock_api)

    # Initial value
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "normal"
    assert entity.attributes["options"] == ["dimmed", "normal", "off"]

    # Set value
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": entity_under_test, "option": "dimmed"},
        blocking=True,
    )
    assert mock_api.device.set_led_mode.call_args == call(2)
