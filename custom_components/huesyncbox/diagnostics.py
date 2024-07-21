"""Diagnostics support for Philips Hue Play HDMI Sync Box integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant

from . import HueSyncBoxConfigEntry

KEYS_TO_REDACT_CONFIG_ENTRY = [CONF_ACCESS_TOKEN, CONF_UNIQUE_ID]
KEYS_TO_REDACT_API = ["uniqueId", "bridgeUniqueId", "ssid"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: HueSyncBoxConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}

    data["config_entry"] = async_redact_data(
        entry.as_dict(), KEYS_TO_REDACT_CONFIG_ENTRY
    )

    if runtime_data := entry.runtime_data:
        data["api"] = {}
        if runtime_data.coordinator.api.last_response is not None:
            data["api"] = async_redact_data(
                runtime_data.coordinator.api.last_response, KEYS_TO_REDACT_API
            )

    return data
