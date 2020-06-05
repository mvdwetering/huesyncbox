"""Code to handle a Philips Hue Play HDMI Sync Box."""
import asyncio

import aiohuesyncbox
import async_timeout
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, LOGGER
from .errors import AuthenticationRequired, CannotConnect

class HueSyncBox:
    """Manages a single Philips Hue Play HDMI Sync Box."""

    def __init__(self, hass, config_entry):
        """Initialize the system."""
        self.config_entry = config_entry
        self.hass = hass
        self.api = None # aiohuesyncbox instance
        self.entity = None # Mediaplayer entity

    async def async_setup(self, tries=0):
        """Set up a huesyncbox based on host parameter."""
        hass = self.hass

        initialized = False
        try:
            self.api = await async_get_aiohuesyncbox_from_entry_data(self.config_entry.data)
            with async_timeout.timeout(10):
                await self.api.initialize()
                initialized = True
        except (aiohuesyncbox.InvalidState, aiohuesyncbox.Unauthorized):
            LOGGER.error("Authorization data for Philips Hue Play HDMI Sync Box %s is invalid. Delete and setup the integration again.", self.config_entry.data["unique_id"])
            return False
        except (asyncio.TimeoutError, aiohuesyncbox.RequestError):
            LOGGER.error("Error connecting to the Philips Hue Play HDMI Sync Box at %s", self.config_entry.data["host"])
            raise ConfigEntryNotReady
        except aiohuesyncbox.AiohuesyncboxException:
            LOGGER.exception("Unknown Philips Hue Play HDMI Sync Box API error occurred")
            raise ConfigEntryNotReady
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unknown error connecting with Philips Hue Play HDMI Sync Box at %s", self.config_entry.data["host"])
            return False
        finally:
            if not initialized:
                await self.api.close()

        huesyncbox = self # Alias for use in async_stop
        async def async_stop(self, event=None) -> None:
            """Unsubscribe from events."""
            await huesyncbox.async_reset()

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop)

        return True

    async def async_reset(self):
        """
        Reset this huesyncbox to default state.
        """
        if self.api is not None:
            await self.api.close()

        return True


async def async_register_aiohuesyncbox(hass, api):
    try:
        with async_timeout.timeout(10):
            return await api.register("home-assistant", hass.config.location_name)
    except (aiohuesyncbox.InvalidState, aiohuesyncbox.Unauthorized):
        raise AuthenticationRequired
    except (asyncio.TimeoutError, aiohuesyncbox.RequestError):
        raise CannotConnect
    except aiohuesyncbox.AiohuesyncboxException:
        LOGGER.exception("Unknown Philips Hue Play HDMI Sync Box error occurred")
        raise CannotConnect

async def async_get_aiohuesyncbox_from_entry_data(entry_data):
    """Create a huesyncbox object from entry data."""
    return aiohuesyncbox.HueSyncBox(
        entry_data["host"],
        entry_data["unique_id"],
        access_token=entry_data.get("access_token"),
        port=entry_data["port"],
        path=entry_data["path"]
    )

async def async_remove_entry_from_huesyncbox(entry):
    with async_timeout.timeout(10):
        async with await async_get_aiohuesyncbox_from_entry_data(entry.data) as api:
            await api.unregister(entry.data['registration_id'])
