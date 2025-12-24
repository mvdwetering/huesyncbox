from unittest.mock import Mock

from homeassistant.core import HomeAssistant

from custom_components.huesyncbox.diagnostics import async_get_config_entry_diagnostics

from .conftest import setup_integration

REDACTED = "**REDACTED**"


async def test_diagnostics(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)
    integration.mock_api.last_response = {
        "uniqueId": "abc",
        "bridgeUniqueId": "def",
        "ssid": "ghi",
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, integration.entry)

    assert "config_entry_data" in diagnostics
    assert diagnostics["config_entry_data"]["unique_id"] == REDACTED
    assert diagnostics["config_entry_data"]["access_token"] == REDACTED

    assert "api" in diagnostics
    assert diagnostics["api"]["uniqueId"] == REDACTED
    assert diagnostics["api"]["bridgeUniqueId"] == REDACTED
    assert diagnostics["api"]["ssid"] == REDACTED


async def test_diagnostics_no_response_yet(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)
    integration.mock_api.last_response = None

    diagnostics = await async_get_config_entry_diagnostics(hass, integration.entry)

    assert "config_entry_data" in diagnostics
    assert diagnostics["config_entry_data"]["unique_id"] == REDACTED
    assert diagnostics["config_entry_data"]["access_token"] == REDACTED

    assert "api" in diagnostics
    assert diagnostics["api"] == {}


async def test_diagnostics_not_setup(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)
    integration.entry.runtime_data = None

    diagnostics = await async_get_config_entry_diagnostics(hass, integration.entry)

    assert "config_entry_data" in diagnostics
    assert diagnostics["config_entry_data"]["unique_id"] == REDACTED
    assert diagnostics["config_entry_data"]["access_token"] == REDACTED

    assert "api" not in diagnostics
