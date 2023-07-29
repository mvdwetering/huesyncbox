"""The Philips Hue Play HDMI Sync Box integration."""

from datetime import timedelta
import aiohuesyncbox
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers import device_registry
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, MANUFACTURER_NAME, LOGGER

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SWITCH]


class HueSyncBoxCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api: aiohuesyncbox.HueSyncBox):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Name of the data. For logging purposes.
            name="HueSyncBox data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=2),
        )
        self.api = api

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(5):

                old_device = self.api.device
                await self.api.update()

                if old_device != self.api.device:
                    await update_device_registry(self.hass, self.config_entry, self.api)

                return self.api
        except aiohuesyncbox.Unauthorized as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except aiohuesyncbox.RequestError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


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


    await update_device_registry(hass, entry, api)

    coordinator = HueSyncBoxCoordinator(hass, api)

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.close()

    return unload_ok
