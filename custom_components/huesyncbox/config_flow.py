"""Config flow for Philips Hue Play HDMI Sync Box integration."""
import asyncio
from dataclasses import asdict, dataclass
import logging
from typing import Any

import aiohuesyncbox
import voluptuous as vol  # type: ignore

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_NAME,
    CONF_PATH,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_PORT, DOMAIN, REGISTRATION_ID

_LOGGER = logging.getLogger(__name__)

USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_UNIQUE_ID): str,
    }
)


@dataclass
class ConnectionInfo:
    host: str
    unique_id: str
    access_token: str | None = None
    registration_id: str | None = None
    port: int = 443
    path: str = "/api"


def entry_data_from_connection_info(connection_info: ConnectionInfo):
    return {
        CONF_HOST: connection_info.host,
        CONF_UNIQUE_ID: connection_info.unique_id,
        CONF_PORT: connection_info.port,
        CONF_PATH: connection_info.path,
    }


async def try_connection(connection_info: ConnectionInfo):
    """Validate the connection_info allows us to connect."""

    async with aiohuesyncbox.HueSyncBox(
        connection_info.host,
        connection_info.unique_id,
        connection_info.access_token,
        connection_info.port,
        connection_info.path,
    ) as huesyncbox:
        try:
            # Just see if the connection works
            await huesyncbox.is_registered()
        except aiohuesyncbox.Unauthorized:
            raise InvalidAuth
        except aiohuesyncbox.RequestError:
            raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Philips Hue Play HDMI Sync Box."""

    VERSION = 2

    link_task: asyncio.Task | None = None
    reauth_entry: config_entries.ConfigEntry | None = None

    connection_info: ConnectionInfo
    device_name = "Default syncbox name"

    @callback
    def async_remove(self) -> None:
        _LOGGER.debug("async_remove, %s", self.link_task is not None)
        if self.link_task:
            self.link_task.cancel()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("async_step_user, %s", user_input)
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=USER_DATA_SCHEMA,
                last_step=False,
            )

        connection_info = ConnectionInfo(
            user_input[CONF_HOST], user_input[CONF_UNIQUE_ID]
        )

        errors = {}

        try:
            await try_connection(connection_info)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            # Should not occur as we don't have accesstoken
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Protect against setting up existing entries
            # But do update the entry so it is possible to update host
            # for entries that were setup manually
            await self.async_set_unique_id(connection_info.unique_id)
            self._abort_if_unique_id_configured(
                updates=entry_data_from_connection_info(connection_info)
            )

            self.connection_info = connection_info
            return await self.async_step_link()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                USER_DATA_SCHEMA, asdict(connection_info)
            ),
            errors=errors,
            last_step=False,
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        _LOGGER.debug("async_step_zeroconf, %s", discovery_info)

        connection_info = ConnectionInfo(
            discovery_info.host,
            discovery_info.properties["uniqueid"],
            port=discovery_info.port or DEFAULT_PORT,
            path=discovery_info.properties["path"],
        )
        # Also available, do we need it?
        # "devicetype": discovery_info.properties["devicetype"],  value is HSB001

        await self.async_set_unique_id(connection_info.unique_id)
        self._abort_if_unique_id_configured(
            updates=entry_data_from_connection_info(connection_info),
            reload_on_update=True,  # This is the default, but make it more visible
        )

        self.device_name = discovery_info.properties["name"]
        self.connection_info = connection_info

        # This makes sure that the name of the box appears in the card with the discovered device
        self.context.update({"title_placeholders": {CONF_NAME: self.device_name}})

        # Can't directly go to link step as it will immediately start trying to link
        # and it seems to get stuck. Go through intermediate dialog like with reauth.
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(self, user_input=None) -> FlowResult:
        """Dialog that informs the user that device is found and needs to be linked."""
        _LOGGER.debug("async_step_zeroconf_confirm, %s", user_input)
        if user_input is None:
            return self.async_show_form(step_id="zeroconf_confirm", last_step=False)
        return await self.async_step_link()

    async def _async_register(
        self, ha_instance_name: str, connection_info: ConnectionInfo
    ):
        _LOGGER.debug("_async_register, %s", connection_info)
        cancelled = False

        try:
            async with aiohuesyncbox.HueSyncBox(
                connection_info.host,
                connection_info.unique_id,
                connection_info.access_token,
                connection_info.port,
                connection_info.path,
            ) as huesyncbox:
                registration_info = None
                while not registration_info:
                    try:
                        registration_info = await huesyncbox.register(
                            "Home Assistant", ha_instance_name
                        )
                    except aiohuesyncbox.InvalidState:
                        # This is expected as syncbox will be in invalid state until button is pressed
                        pass
                    await asyncio.sleep(1)

                self.connection_info.access_token = registration_info[CONF_ACCESS_TOKEN]
                self.connection_info.registration_id = registration_info[
                    REGISTRATION_ID
                ]

                await huesyncbox.initialize()
                self.device_name = huesyncbox.device.name

                return True

        except aiohuesyncbox.RequestError:
            return False
        except aiohuesyncbox.AiohuesyncboxException:
            _LOGGER.exception("Unknown Philips Hue Play HDMI Sync Box error occurred")
            return False
        except asyncio.CancelledError:
            _LOGGER.debug("_async_register, %s", "asyncio.CancelledError")
            cancelled = True
        finally:
            # Only gets cancelled when flow is removed, don't call things on flow after that
            _LOGGER.debug("_async_register, %s, %s", "finally", cancelled)
            if not cancelled:
                # Continue the flow after show progress when the task is done.
                # To avoid a potential deadlock we create a new task that continues the flow.
                # The task must be completely done so the flow can await the task
                # if needed and get the task result.
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
                )

    async def async_step_link(self, user_input=None) -> FlowResult:
        """Handle the linking step."""
        _LOGGER.debug("async_step_link, %s", user_input)
        assert self.connection_info

        if not self.link_task:
            self.link_task = self.hass.async_create_task(
                self._async_register(
                    self.hass.config.location_name, self.connection_info
                )
            )

            return self.async_show_progress(
                step_id="link",
                progress_action="wait_for_button",
            )

        registered = False
        try:
            registered = self.link_task.result()
        except asyncio.CancelledError:
            # Was cancelled, so not registered
            pass
        except asyncio.InvalidStateError:
            # Was not done, so not registered, cancel it
            self.link_task.cancel()

        next_step_id = "finish" if registered else "abort"
        return self.async_show_progress_done(next_step_id=next_step_id)

    async def async_step_finish(self, user_input=None) -> FlowResult:
        """Finish flow"""
        _LOGGER.debug("async_step_finish, %s", user_input)
        assert self.connection_info

        if self.reauth_entry:
            self.hass.config_entries.async_update_entry(
                self.reauth_entry, data=asdict(self.connection_info)
            )
            await self.hass.config_entries.async_reload(self.reauth_entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=self.device_name, data=asdict(self.connection_info)
        )

    async def async_step_abort(self, user_input=None) -> FlowResult:
        """Abort flow"""
        _LOGGER.debug("async_step_abort, %s", user_input)
        return self.async_abort(reason="connection_failed")

    async def async_step_reauth(self, user_input=None):
        """Reauth is triggered when token is not valid anymore, retrigger link flow."""
        _LOGGER.debug("async_step_reauth, %s", user_input)
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        assert self.reauth_entry is not None

        self.connection_info = ConnectionInfo(
            self.reauth_entry.data[CONF_HOST],
            self.reauth_entry.data[CONF_UNIQUE_ID],
            self.reauth_entry.data[CONF_ACCESS_TOKEN],
            self.reauth_entry.data[REGISTRATION_ID],
            self.reauth_entry.data[CONF_PORT],
            self.reauth_entry.data[CONF_PATH],
        )

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        _LOGGER.debug("async_step_reauth_confirm, %s", user_input)
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm", last_step=False)
        return await self.async_step_link()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
