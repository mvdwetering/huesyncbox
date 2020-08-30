"""The Philips Hue Play HDMI Sync Box integration."""
import asyncio
import logging
import json
import os

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (config_validation as cv)
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import async_extract_entity_ids
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_BRIGHTNESS_STEP

from .huesyncbox import HueSyncBox, async_remove_entry_from_huesyncbox
from .const import DOMAIN, LOGGER, ATTR_SYNC, ATTR_SYNC_TOGGLE, ATTR_MODE, ATTR_MODE_NEXT, ATTR_MODE_PREV, MODES, ATTR_INTENSITY, ATTR_INTENSITY_NEXT, ATTR_INTENSITY_PREV, INTENSITIES, ATTR_INPUT, ATTR_INPUT_NEXT, ATTR_INPUT_PREV, INPUTS, SERVICE_SET_SYNC_STATE, SERVICE_SET_BRIGHTNESS, SERVICE_SET_MODE, SERVICE_SET_INTENSITY

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["media_player"]

HUESYNCBOX_SET_STATE_SCHEMA = make_entity_service_schema(
    {
        vol.Optional(ATTR_SYNC): cv.boolean,
        vol.Optional(ATTR_SYNC_TOGGLE): cv.boolean,
        vol.Optional(ATTR_BRIGHTNESS): cv.small_float,
        vol.Optional(ATTR_BRIGHTNESS_STEP): vol.All(vol.Coerce(float), vol.Range(min=-1, max=1)),
        vol.Optional(ATTR_MODE): vol.In(MODES),
        vol.Optional(ATTR_MODE_NEXT): cv.boolean,
        vol.Optional(ATTR_MODE_PREV): cv.boolean,
        vol.Optional(ATTR_INTENSITY): vol.In(INTENSITIES),
        vol.Optional(ATTR_INTENSITY_NEXT): cv.boolean,
        vol.Optional(ATTR_INTENSITY_PREV): cv.boolean,
        vol.Optional(ATTR_INPUT): vol.In(INPUTS),
        vol.Optional(ATTR_INPUT_NEXT): cv.boolean,
        vol.Optional(ATTR_INPUT_PREV): cv.boolean,
    }
)

HUESYNCBOX_SET_BRIGHTNESS_SCHEMA = make_entity_service_schema(
    {vol.Required(ATTR_BRIGHTNESS): cv.small_float}
)

HUESYNCBOX_SET_MODE_SCHEMA = make_entity_service_schema(
    {vol.Required(ATTR_MODE): vol.In(MODES)}
)

HUESYNCBOX_SET_INTENSITY_SCHEMA = make_entity_service_schema(
    {vol.Required(ATTR_INTENSITY): vol.In(INTENSITIES), vol.Optional(ATTR_MODE): vol.In(MODES)}
)

services_registered = False

async def async_setup(hass: HomeAssistant, config: dict):
    """
    Set up the Philips Hue Play HDMI Sync Box integration.
    Only supporting zeroconf, so nothing to do here.
    """
    hass.data[DOMAIN] = {}

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
    LOGGER.debug("async_setup_entry len(hass.data[DOMAIN].items()) = %s" % len(hass.data[DOMAIN].items()))

    global services_registered
    if not services_registered:
        await async_register_services(hass)
        services_registered = True

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
        global services_registered
        services_registered = False

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Best effort cleanup. User might not even have the device anymore or had it factory reset.
    # Note that the entry already has been unloaded.
    try:
        await async_remove_entry_from_huesyncbox(entry)
    except Exception as e:
        LOGGER.debug("Unregistering Philips Hue Play HDMI Sync Box failed: %s ", e)


async def async_register_services(hass: HomeAssistant):
    LOGGER.debug("async_register_services")

    async def async_set_sync_state(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_sync_state(call.data)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_SYNC_STATE, async_set_sync_state, schema=HUESYNCBOX_SET_STATE_SCHEMA
    )

    async def async_set_sync_mode(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_sync_mode(call.data.get(ATTR_MODE))

    hass.services.async_register(
        DOMAIN, SERVICE_SET_MODE, async_set_sync_mode, schema=HUESYNCBOX_SET_MODE_SCHEMA
    )

    async def async_set_intensity(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_intensity(call.data.get(ATTR_INTENSITY), call.data.get(ATTR_MODE, None))

    hass.services.async_register(
        DOMAIN, SERVICE_SET_INTENSITY, async_set_intensity, schema=HUESYNCBOX_SET_INTENSITY_SCHEMA
    )

    async def async_set_brightness(call):
        entity_ids = await async_extract_entity_ids(hass, call)
        for _, entry in hass.data[DOMAIN].items():
            if entry.entity and entry.entity.entity_id in entity_ids:
                await entry.entity.async_set_brightness(call.data.get(ATTR_BRIGHTNESS))

    hass.services.async_register(
        DOMAIN, SERVICE_SET_BRIGHTNESS, async_set_brightness, schema=HUESYNCBOX_SET_BRIGHTNESS_SCHEMA
    )


async def async_unregister_services(hass):
    LOGGER.debug("async_unregister_services")
    hass.services.async_remove(DOMAIN, SERVICE_SET_SYNC_STATE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_SET_MODE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_INTENSITY)
