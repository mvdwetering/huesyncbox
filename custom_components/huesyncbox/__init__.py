"""The Philips Hue Play HDMI Sync Box integration."""

import aiohuesyncbox

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers import device_registry

from .const import DOMAIN, MANUFACTURER_NAME

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = []


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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Philips Hue Play HDMI Sync Box from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = aiohuesyncbox.HueSyncBox(
        entry.data["host"],
        entry.data["unique_id"],
        access_token=entry.data.get("access_token"),
        port=entry.data["port"],
        path=entry.data["path"],
    )        
    
    try:
        await api.initialize()
    except aiohuesyncbox.Unauthorized as err:
        raise ConfigEntryAuthFailed(err) from err
    except aiohuesyncbox.RequestError as err:
        raise ConfigEntryError(err) from err

    hass.data[DOMAIN][entry.entry_id] = api

    await update_device_registry(hass, entry, api)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.close()

    return unload_ok
