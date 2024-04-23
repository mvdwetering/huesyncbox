"""Coordinator for the Philips Hue Play HDMI Sync Box integration."""

import asyncio
import aiohuesyncbox

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import COORDINATOR_UPDATE_INTERVAL, LOGGER
from .helpers import update_config_entry_title, update_device_registry

MAX_CONSECUTIVE_ERRORS = 5

class HueSyncBoxCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api: aiohuesyncbox.HueSyncBox):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Name of the data. For logging purposes.
            name=f"Philips Hue Play HDMI Sync Box ({api.device.name} at {api.device.ip_address})",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self.api = api
        self._consecutive_errors = 0

    def _is_consecutive_error_reached(self):
        self._consecutive_errors += 1
        LOGGER.debug("Consecutive errors = %s", self._consecutive_errors)
        return self._consecutive_errors >= MAX_CONSECUTIVE_ERRORS

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(5):

                old_device = self.api.device
                await self.api.update()
                self._consecutive_errors = 0

                if old_device != self.api.device:
                    await update_device_registry(self.hass, self.config_entry, self.api)
                    update_config_entry_title(
                        self.hass, self.config_entry, self.api.device.name
                    )

        except aiohuesyncbox.Unauthorized as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except aiohuesyncbox.RequestError as err:
            LOGGER.debug("aiohuesyncbox.RequestError while updating data: %s", err)
            if self._is_consecutive_error_reached():
                raise UpdateFailed(err) from err
        except asyncio.TimeoutError:
            LOGGER.debug("asyncio.TimeoutError while updating data")
            if self._is_consecutive_error_reached():
                raise

        return self.api
