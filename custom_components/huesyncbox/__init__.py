"""The Philips Hue Play HDMI Sync Box integration."""
import asyncio
import logging
import json
import os

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.generated.zeroconf import ZEROCONF
from homeassistant.helpers import (config_validation as cv)
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import async_extract_entity_ids

from .huesyncbox import HueSyncBox, async_remove_entry_from_huesyncbox
from .const import DOMAIN, LOGGER, MANUFACTURER_NAME, HUESYNCBOX_ATTR_BRIGHTNESS, HUESYNCBOX_ATTR_MODE, HUESYNCBOX_ATTR_INTENSITY, HUESYNCBOX_INTENSITIES, HUESYNCBOX_MODES

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["media_player"]

HUESYNCBOX_INTENSITIES = ['subtle', 'moderate', 'high', 'intense']
HUESYNCBOX_MODES = ['video', 'music', 'game']

SERVICE_HUESYNCBOX_SET_BRIGHTNESS = 'set_brightness'

HUESYNCBOX_SET_BRIGHTNESS_SCHEMA = make_entity_service_schema(
    {vol.Required(HUESYNCBOX_ATTR_BRIGHTNESS): cv.small_float}
)

SERVICE_HUESYNCBOX_SET_MODE = 'set_mode'
HUESYNCBOX_SET_MODE_SCHEMA = make_entity_service_schema(
    {vol.Required(HUESYNCBOX_ATTR_MODE): vol.In(HUESYNCBOX_MODES)}
)

SERVICE_HUESYNCBOX_SET_INTENSITY = 'set_intensity'
HUESYNCBOX_SET_INTENSITY_SCHEMA = make_entity_service_schema(
    {vol.Required(HUESYNCBOX_ATTR_INTENSITY): vol.In(HUESYNCBOX_INTENSITIES), vol.Optional(HUESYNCBOX_ATTR_MODE): vol.In(HUESYNCBOX_MODES)}
)

def _register_zeroconf_hack():
    """ Dirty hack to get our zeroconf info into the generated file without actually generating it (which is not possible for custom components) """
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "manifest.json")) as manifest_file:
        manifest = json.load(manifest_file)
        for service in manifest["zeroconf"]:
            if service not in ZEROCONF:
                ZEROCONF[service] = [DOMAIN]


async def async_setup(hass: HomeAssistant, config: dict):
    """
    Set up the Philips Hue Play HDMI Sync Box integration.
    Only supporting zeroconf, so nothing to do here.
    """
    hass.data[DOMAIN] = {}

    # This seems to be the earliest place to register with zeroconf
    # Unfortunately this requires an entry in the configuration.yaml
    # Apperently this is still early enough so the this list has not been processed yet
    _register_zeroconf_hack()

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up a config entry for Philips Hue Play HDMI Sync Box."""
    huesyncbox = HueSyncBox(hass, entry)
    hass.data[DOMAIN][entry.data["unique_id"]] = huesyncbox

    if not await huesyncbox.async_setup():
        return False

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    # Register services on first entry
    if len(hass.data[DOMAIN].items()) == 1:
        await async_register_services(hass)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    if unload_ok:
        huesyncbox = hass.data[DOMAIN].pop(entry.data["unique_id"])
        await huesyncbox.async_reset()

    # Unregister services when last entry is unloaded
    if len(hass.data[DOMAIN].items()) == 0:
        await async_unregister_services(hass)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Best effort cleanup. User might not even have the device anymore or had it factory reset.
    # Note that the entry already has been unloaded.
    try:
        await async_remove_entry_from_huesyncbox(entry)
    except Exception as e:
        LOGGER.debug("Unregistering Philips Hue Play HDMI Sync Box failed: %s ", e)


async def async_register_services(hass: HomeAssistant):

    async def async_set_sync_mode(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_sync_mode(call.data.get(HUESYNCBOX_ATTR_MODE))

    hass.services.async_register(
        DOMAIN, SERVICE_HUESYNCBOX_SET_MODE, async_set_sync_mode, schema=HUESYNCBOX_SET_MODE_SCHEMA
    )

    async def async_set_intensity(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_intensity(call.data.get(HUESYNCBOX_ATTR_INTENSITY), call.data.get(HUESYNCBOX_ATTR_MODE, None))

    hass.services.async_register(
        DOMAIN, SERVICE_HUESYNCBOX_SET_INTENSITY, async_set_intensity, schema=HUESYNCBOX_SET_INTENSITY_SCHEMA
    )

    async def async_set_brightness(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_brightness(call.data.get(HUESYNCBOX_ATTR_BRIGHTNESS))

    hass.services.async_register(
        DOMAIN, SERVICE_HUESYNCBOX_SET_BRIGHTNESS, async_set_brightness, schema=HUESYNCBOX_SET_BRIGHTNESS_SCHEMA
    )


async def async_unregister_services(hass):
    hass.services.async_remove(DOMAIN, SERVICE_HUESYNCBOX_SET_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_HUESYNCBOX_SET_MODE)
    hass.services.async_remove(DOMAIN, SERVICE_HUESYNCBOX_SET_INTENSITY)
