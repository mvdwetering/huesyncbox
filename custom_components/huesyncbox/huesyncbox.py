"""Code to handle a Philips Hue Play HDMI Sync Box."""
import asyncio
import textwrap

import aiohuesyncbox
import async_timeout
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import DOMAIN, LOGGER, MANUFACTURER_NAME
from .errors import AuthenticationRequired, CannotConnect
from .helpers import log_entry_data, redacted


class PhilipsHuePlayHdmiSyncBox:
    """Manages a single Philips Hue Play HDMI Sync Box."""

    def __init__(self, hass, config_entry):
        """Initialize the system."""
        self.config_entry = config_entry
        self.hass = hass
        self.api = None  # aiohuesyncbox instance
        self.entity = None  # Mediaplayer entity

    def __str__(self):
        output = ""
        output += f"{self.config_entry}\n"
        output += f"{self.api}\n"
        output += f"{self.entity}\n"
        return output

    async def async_setup(self, tries=0):
        """Set up a huesyncbox based on host parameter."""
        hass = self.hass

        initialized = False
        try:
            self.api = await async_get_aiohuesyncbox_from_entry_data(
                self.config_entry.data
            )
            with async_timeout.timeout(10):
                await self.api.initialize()
                await self.async_update_registered_device_info()  # Info might have changed while HA was not running
                if self.api.hue.connection_state not in [
                    "connected",
                    "streaming",
                    "busy",
                ]:
                    LOGGER.warning(
                        "The Philips Hue Play HDMI Sync Box does not seems to have a connection to the Hue Bridge. Use the Hue Sync app to diagnose/fix the issue."
                    )
                initialized = True
        except (aiohuesyncbox.InvalidState, aiohuesyncbox.Unauthorized):
            LOGGER.error(
                "Authorization data for Philips Hue Play HDMI Sync Box %s is invalid. Delete and setup the integration again.",
                redacted(self.config_entry.data["unique_id"]),
            )
            return False
        except (asyncio.TimeoutError, aiohuesyncbox.RequestError) as ex:
            LOGGER.error(
                "Error connecting to the Philips Hue Play HDMI Sync Box at %s",
                self.config_entry.data["host"],
            )
            raise ConfigEntryNotReady from ex
        except aiohuesyncbox.AiohuesyncboxException as ex:
            LOGGER.exception(
                "Unknown Philips Hue Play HDMI Sync Box API error occurred"
            )
            raise ConfigEntryNotReady from ex
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception(
                "Unknown error connecting with Philips Hue Play HDMI Sync Box at %s",
                self.config_entry.data["host"],
            )
            return False
        finally:
            if not initialized:
                await self.api.close()

        huesyncbox = self  # Alias for use in async_stop

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

    async def async_update_registered_device_info(self):
        """
        Update device registry with info from the API
        """
        if self.api is not None:
            device_registry = (
                await self.hass.helpers.device_registry.async_get_registry()
            )
            # Get or create also updates existing entries
            device_registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={(DOMAIN, self.api.device.unique_id)},
                name=self.api.device.name,
                manufacturer=MANUFACTURER_NAME,
                model=self.api.device.device_type,
                sw_version=self.api.device.firmware_version,
                # Uniqueid seems to be the mac. Adding the connection allows other integrations
                # like e.g. Mikrotik Router to link their entities to this device
                connections={(CONNECTION_NETWORK_MAC, self.api.device.unique_id)},
            )

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=self.api.device.name,
            )

        return True


async def async_register_aiohuesyncbox(hass, api: aiohuesyncbox.HueSyncBox):
    """Try to register HA with the syncbox"""
    try:
        with async_timeout.timeout(60):
            registration_info = None
            while not registration_info:
                try:
                    registration_info = await api.register(
                        "Home Assistant", hass.config.location_name
                    )
                except aiohuesyncbox.InvalidState:
                    # This is expected as syncbox will be in invalid state until button is pressed
                    pass
                await asyncio.sleep(1)
            return registration_info
    except asyncio.TimeoutError as ex:
        LOGGER.warning("Registration timed out")
        raise AuthenticationRequired from ex
    except aiohuesyncbox.Unauthorized as ex:
        raise AuthenticationRequired from ex
    except aiohuesyncbox.RequestError as ex:
        raise CannotConnect from ex
    except aiohuesyncbox.AiohuesyncboxException as ex:
        LOGGER.exception("Unknown Philips Hue Play HDMI Sync Box error occurred")
        raise CannotConnect from ex


async def async_get_aiohuesyncbox_from_entry_data(entry_data):
    """Create a huesyncbox object from entry data."""

    LOGGER.debug(
        "%s async_get_aiohuesyncbox_from_entry_data\nentry_data:\n%s",
        __name__,
        textwrap.indent(log_entry_data(entry_data), "  "),
    )

    return aiohuesyncbox.HueSyncBox(
        entry_data["host"],
        entry_data["unique_id"],
        access_token=entry_data.get("access_token"),
        port=entry_data["port"],
        path=entry_data["path"],
    )


async def async_remove_entry_from_huesyncbox(entry):
    """Remove registration entry from syncbox"""
    with async_timeout.timeout(10):
        async with await async_get_aiohuesyncbox_from_entry_data(entry.data) as api:
            await api.unregister(entry.data["registration_id"])


async def async_retry_if_someone_else_is_syncing(hsb: PhilipsHuePlayHdmiSyncBox, func):
    """Decorator to retry a request is something else is already syncing on the connected bridge"""
    try:
        await func()
    except aiohuesyncbox.InvalidState:
        # Most likely another application is already syncing to the bridge
        # Since there is no way to ask the user what to do just
        # stop the active application and try again
        for group in hsb.api.hue.groups:
            if group.active:
                LOGGER.info(
                    "Deactivating syncing on '%s' for entertainment area '%s' with name '%s' in use by '%s'",
                    hsb.api.device.name,
                    group.id,
                    group.name,
                    group.owner,
                )
                await hsb.api.hue.set_group_active(group.id, active=False)
        await func()
