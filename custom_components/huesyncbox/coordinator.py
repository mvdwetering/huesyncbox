"""Coordinator for the Philips Hue Play HDMI Sync Box integration."""

from datetime import timedelta
import aiohuesyncbox
import async_timeout

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import LOGGER
from .helpers import update_device_registry


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
        """Fetch data from API endpoint."""
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
