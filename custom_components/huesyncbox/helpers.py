"""Helpers for the Philips Hue Play HDMI Sync Box integration."""

from typing import List
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

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
        # Uniqueid seems to be the mac. Adding the connection allows other integrations
        # like e.g. Mikrotik Router to link their entities to this device
        connections={(CONNECTION_NETWORK_MAC, api.device.unique_id)},
    )


def update_config_entry_title(
    hass: HomeAssistant, config_entry: ConfigEntry, new_title: str
):
    hass.config_entries.async_update_entry(config_entry, title=new_title)


async def stop_sync_and_retry_on_invalid_state(async_func, *args, **kwargs):
    try:
        await async_func(*args, **kwargs)
    except aiohuesyncbox.InvalidState:
        # Most likely another application is already syncing to the bridge
        # Since there is no way to ask the user what to do just
        # stop the active application and try again
        api: aiohuesyncbox.HueSyncBox = args[0]
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


class LinearRangeConverter:
    """Converts values from one range to another with a linear thingy (y=ax+b)"""

    def __init__(self, range_1: List[float], range_2: List[float]) -> None:
        self._a = (range_2[1] - range_2[0]) / (range_1[1] - range_1[0])
        self._b = range_2[0] - (self._a * range_1[0])

    def range_2_to_range_1(self, y):
        return (y - self._b) / self._a

    def range_1_to_range_2(self, x):
        return (self._a * x) + self._b


class BrightnessRangeConverter:
    _converter = LinearRangeConverter([1, 100], [0, 200])

    @classmethod
    def ha_to_api(cls, ha_value):
        return round(cls._converter.range_1_to_range_2(ha_value))

    @classmethod
    def api_to_ha(cls, api_value):
        return round(cls._converter.range_2_to_range_1(api_value))


def get_hue_target_from_id(id_: str):
    """Determine API target from id"""
    try:
        return f"groups/{int(id_)}"
    except ValueError:
        return id_


def get_group_from_area_name(api: aiohuesyncbox.HueSyncBox, area_name):
    """Get the group object by entertainment area name."""
    for group in api.hue.groups:
        if group.name == area_name:
            return group
    return None
