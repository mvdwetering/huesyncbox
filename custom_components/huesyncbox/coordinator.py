"""Coordinator for the Philips Hue Play HDMI Sync Box integration."""

import asyncio
from functools import partial
from typing import TYPE_CHECKING

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CALLBACK_TYPE,
    DataUpdateCoordinator,
    UpdateFailed,
)

import aiohuesyncbox

from .const import COORDINATOR_UPDATE_INTERVAL, LOGGER
from .helpers import update_config_entry_title, update_device_registry

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant

MAX_CONSECUTIVE_ERRORS = 5


class HueSyncBoxCoordinator(DataUpdateCoordinator[aiohuesyncbox.HueSyncBox]):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, api: aiohuesyncbox.HueSyncBox) -> None:
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

        self._operating_mode_change_listeners: dict[int, CALLBACK_TYPE] = {}
        self._last_operating_mode_change_listener_id: int = 0


    def _is_consecutive_error_reached(self) -> bool:
        self._consecutive_errors += 1
        LOGGER.debug("Consecutive errors = %s", self._consecutive_errors)
        return self._consecutive_errors >= MAX_CONSECUTIVE_ERRORS

    async def _async_update_data(self) -> aiohuesyncbox.HueSyncBox:
        """Fetch data from API endpoint."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with asyncio.timeout(5):
                old_device = self.api.device
                old_operating_mode = self.api.hue.operating_mode
                await self.api.refresh_data()
                self._consecutive_errors = 0

                if old_device != self.api.device:
                    await update_device_registry(self.hass, self.config_entry, self.api)
                    update_config_entry_title(
                        self.hass, self.config_entry, self.api.device.name
                    )

                if old_operating_mode != self.api.hue.operating_mode and (
                    old_operating_mode is aiohuesyncbox.OperatingMode.STANDALONE
                    or self.api.hue.operating_mode
                    is aiohuesyncbox.OperatingMode.STANDALONE
                ):
                    # Device changed to or from standalone mode, trigger platforms so
                    # they can add/remove entities as needed.
                    self.async_trigger_operating_mode_change_listeners()

        except aiohuesyncbox.Unauthorized as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except aiohuesyncbox.RequestError as err:
            LOGGER.debug("aiohuesyncbox.RequestError while updating data: %s", err)
            if self._is_consecutive_error_reached():
                raise UpdateFailed(err) from err
        except TimeoutError:
            LOGGER.debug("asyncio.TimeoutError while updating data")
            if self._is_consecutive_error_reached():
                raise

        return self.api

    def async_add_operating_mode_change_listener(
        self, update_callback: CALLBACK_TYPE
    ) -> Callable[[], None]:
        """Listen for changes in operating mode."""
        self._last_operating_mode_change_listener_id += 1
        self._operating_mode_change_listeners[self._last_operating_mode_change_listener_id] = update_callback

        return partial(self.__async_remove_operating_mode_change_listener_internal, self._last_operating_mode_change_listener_id)

    def __async_remove_operating_mode_change_listener_internal(self, listener_id: int) -> None:
        """Remove an operating mode change listener."""
        self._operating_mode_change_listeners.pop(listener_id, None)

    def async_trigger_operating_mode_change_listeners(self) -> None:
        """Update all registered operating mode change listeners."""
        for update_callback in list(self._operating_mode_change_listeners.values()):
            try:
                update_callback()
            except Exception:
                self.logger.exception(
                    "Unexpected error updating listener %s for %s",
                    id(update_callback),
                    self.name,
                )
