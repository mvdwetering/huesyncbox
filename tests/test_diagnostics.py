from custom_components.huesyncbox.diagnostics import async_get_config_entry_diagnostics
from homeassistant.core import HomeAssistant

from tests.conftest import setup_integration

REDACTED = "**REDACTED**"


async def test_diagnostics(hass: HomeAssistant, mock_api):

    API_RESPONSE = {"uniqueId": "abc", "bridgeUniqueId": "def", "ssid": "ghi"}

    integration = await setup_integration(hass, mock_api)
    integration.mock_api.last_response = API_RESPONSE

    diagnostics = await async_get_config_entry_diagnostics(hass, integration.entry)

    assert "config_entry" in diagnostics
    assert diagnostics["config_entry"]["data"]["unique_id"] == REDACTED
    assert diagnostics["config_entry"]["data"]["access_token"] == REDACTED
    
    assert "api" in diagnostics
    assert diagnostics["api"]["uniqueId"] == REDACTED
    assert diagnostics["api"]["bridgeUniqueId"] == REDACTED
    assert diagnostics["api"]["ssid"] == REDACTED
