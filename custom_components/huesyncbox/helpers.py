"""Helpers for the Philips Hue Play HDMI Sync Box integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from .const import DOMAIN, LOGGER, MANUFACTURER_NAME

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


async def stop_sync_and_retry_on_invalid_state(async_func, *args, **kwargs):
    try:
        await async_func(*args, **kwargs)
    except aiohuesyncbox.InvalidState:
        # Most likely another application is already syncing to the bridge
        # Since there is no way to ask the user what to do just
        # stop the active application and try again
        api:aiohuesyncbox.HueSyncBox = args[0]
        for group in api.hue.groups:
            if group.active:
                LOGGER.info(
                    "%s: Deactivating syncing on bridge '%s' for entertainment area '%s' with name '%s' in use by '%s'",
                    api.device.name,
                    api.hue.bridge_unique_id,
                    group.id,
                    group.name,
                    group.owner,
                )
                await api.hue.set_group_active(group.id, active=False)
                await async_func(*args, **kwargs)
                break
