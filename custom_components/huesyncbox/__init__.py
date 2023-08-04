"""The Philips Hue Play HDMI Sync Box integration."""
import aiohuesyncbox
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError

from .services import async_register_services, async_unregister_services

from .const import (
    DOMAIN,
    LOGGER,
)
from .coordinator import HueSyncBoxCoordinator
from .helpers import update_device_registry

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Philips Hue Play HDMI Sync Box from a config entry."""

    api = aiohuesyncbox.HueSyncBox(
        entry.data["host"],
        entry.data["unique_id"],
        access_token=entry.data.get("access_token"),
        port=entry.data["port"],
        path=entry.data["path"],
    )

    initialized = False
    try:
        await api.initialize()
        initialized = True
    except aiohuesyncbox.Unauthorized as err:
        raise ConfigEntryAuthFailed(err) from err
    except aiohuesyncbox.RequestError as err:
        raise ConfigEntryError(err) from err
    finally:
        if not initialized:
            await api.close()

    await update_device_registry(hass, entry, api)

    coordinator = HueSyncBoxCoordinator(hass, api)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

        if len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN)
            await async_unregister_services(hass)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Best effort cleanup. User might not even have the device anymore or had it factory reset.
    # Note that the entry already has been unloaded, so need to create API again
    try:
        async with async_timeout.timeout(10):
            async with aiohuesyncbox.HueSyncBox(
                entry.data["host"],
                entry.data["unique_id"],
                access_token=entry.data.get("access_token"),
                port=entry.data["port"],
                path=entry.data["path"],
            ) as api:
                await api.unregister(entry.data["registration_id"])
    except Exception as e:
        LOGGER.info(
            "Removing registration from Philips Hue Play HDMI Sync Box failed: %s ", e
        )
