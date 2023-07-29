"""Helpers for the Philips Hue Play HDMI Sync Box integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from .const import DOMAIN, MANUFACTURER_NAME

import aiohuesyncbox


async def update_device_registry(
    hass: HomeAssistant, config_entry: ConfigEntry, api: aiohuesyncbox.HueSyncBox
):
    # Add device explicitly to registry so other entities just have to report the identifier to link up
    registry = device_registry.async_get(hass)

    registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, api.device.unique_id)},
        manufacturer=MANUFACTURER_NAME,
        name=api.device.name,
        model=api.device.device_type,
        sw_version=api.device.firmware_version,
    )
