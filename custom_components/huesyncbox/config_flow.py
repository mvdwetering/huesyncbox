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
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_PATH,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    host: str
    unique_id: str
    access_token: str | None = None
    registration_id: str | None = None
    port: int = 443
    path: str = "/api"


def get_user_data_schema(connection_info: ConnectionInfo):
    return vol.Schema(
        {
            vol.Required(
                CONF_IP_ADDRESS, default=connection_info.host or vol.UNDEFINED # type: ignore
            ): str,
            vol.Required(
                CONF_UNIQUE_ID, default=connection_info.unique_id or vol.UNDEFINED # type: ignore
            ): str,
        }
    )


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
        # Is registered should not throw Unauthorized
        except aiohuesyncbox.Unauthorized:
            raise InvalidAuth
        except aiohuesyncbox.RequestError:
            raise CannotConnect

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Philips Hue Play HDMI Sync Box."""

    VERSION = 1

    link_task:asyncio.Task|None = None

    connection_info: ConnectionInfo
    device_name = "Default syncbox name"

    @callback
    def async_remove(self) -> None:
        if self.link_task:
            self.link_task.cancel()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=get_user_data_schema(ConnectionInfo("", "")),
                last_step=False,
            )

        connection_info = ConnectionInfo(
            user_input[CONF_IP_ADDRESS], user_input[CONF_UNIQUE_ID]
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
            data_schema=get_user_data_schema(connection_info),
            errors=errors,
            last_step=False,
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""

        connection_info = ConnectionInfo(
            discovery_info.host,
            discovery_info.properties["uniqueid"],
            port=discovery_info.port or DEFAULT_PORT,
            path=discovery_info.properties["path"],
        )
        # TODO: Also available, do we need it?
        # "name": discovery_info.properties["name"],
        # "devicetype": discovery_info.properties["devicetype"],

        await self.async_set_unique_id(connection_info.unique_id)
        self._abort_if_unique_id_configured(
            updates=entry_data_from_connection_info(connection_info),
            reload_on_update=True,  # This is the default, but make it more visible
        )

        self.connection_info = connection_info
        return await self.async_step_link()

    async def _async_register(
        self, ha_instance_name: str, connection_info: ConnectionInfo
    ):
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

                self.connection_info.access_token = registration_info["access_token"]
                self.connection_info.registration_id = registration_info[
                    "registration_id"
                ]

                await huesyncbox.initialize()
                self.device_name = huesyncbox.device.name

        # except aiohuesyncbox.Unauthorized as ex:
        #     raise InvalidAuth from ex
        except aiohuesyncbox.RequestError as ex:
            raise CannotConnect from ex
        except aiohuesyncbox.AiohuesyncboxException as ex:
            _LOGGER.exception("Unknown Philips Hue Play HDMI Sync Box error occurred")
            raise CannotConnect from ex
        except asyncio.CancelledError:
            cancelled = True
        finally:
            # Only gets cancelled when flow is removed, don't call things on flow after that
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

        return self.async_show_progress_done(next_step_id="finish")

    async def async_step_finish(self, user_input=None) -> FlowResult:
        """Finish flow"""
        assert self.connection_info
        return self.async_create_entry(
            title=self.device_name, data=asdict(self.connection_info)
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
