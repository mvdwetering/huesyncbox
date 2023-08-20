"""Diagnostics support for Philips Hue Play HDMI Sync Box integration."""
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_UNIQUE_ID

from .coordinator import HueSyncBoxCoordinator

from .const import DOMAIN

KEYS_TO_REDACT_CONFIG_ENTRY = [CONF_ACCESS_TOKEN, CONF_UNIQUE_ID]
KEYS_TO_REDACT_API = ["uniqueId", "bridgeUniqueId", "ssid"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = {}

    data["config_entry"] = async_redact_data(
        entry.as_dict(), KEYS_TO_REDACT_CONFIG_ENTRY
    )

    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN].get(entry.entry_id, None)
    if coordinator:
        data["api"] = {}
        if coordinator.api.last_response is not None:
            data["api"] = async_redact_data(
                coordinator.api.last_response, KEYS_TO_REDACT_API
            )

    return data
