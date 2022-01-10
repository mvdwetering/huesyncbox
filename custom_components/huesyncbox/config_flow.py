"""Config flow for Philips Hue Play HDMI Sync Box integration."""
from __future__ import annotations

import textwrap

from voluptuous import Required, Schema

from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.const import CONF_IP_ADDRESS, CONF_UNIQUE_ID
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, LOGGER  # pylint:disable=unused-import
from .errors import AuthenticationRequired, CannotConnect
from .helpers import log_entry_data, redacted
from .huesyncbox import (
    async_get_aiohuesyncbox_from_entry_data,
    async_register_aiohuesyncbox,
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Philips Hue Play HDMI Sync Box."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""

    async def async_step_user(self, user_input: ConfigType | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=Schema(
                    {
                        Required(CONF_IP_ADDRESS): str,
                        Required(CONF_UNIQUE_ID): str,
                    }
                ),
                errors=None,
            )

        entry_info = {
            "host": user_input[CONF_IP_ADDRESS],
            "port": 443,
            "path": "/api",
            "unique_id": user_input[CONF_UNIQUE_ID],
            "name": "Hue Sync Box",
            "devicetype": "HSB1",
        }

        return await self.async_step_check(entry_info)

    async def async_step_link(self, user_input: ConfigType | None = None) -> FlowResult:
        """
        Attempt to link with the huesyncbox.
        We will only end up in this step when the token is invalid.
        """
        if user_input is None:
            return self.async_show_form(step_id="link")

        errors = {}

        try:
            async with await async_get_aiohuesyncbox_from_entry_data(
                self.context
            ) as api:
                result = await async_register_aiohuesyncbox(self.hass, api)
                self.context["access_token"] = result["access_token"]
                self.context["registration_id"] = result["registration_id"]
            return await self._async_create_entry_from_context()
        except AuthenticationRequired:
            errors["base"] = "register_failed"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception(
                "Unknown error connecting to the Philips Hue Play HDMI Sync Box '%s' at %s",
                redacted(self.context["unique_id"]),
                self.context["host"],
            )
            errors["base"] = "unknown"

        return self.async_show_form(step_id="link", errors=errors)

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""

        entry_info = {
            "host": discovery_info.host,
            "port": discovery_info.port,
            "path": discovery_info.properties["path"],
            "unique_id": discovery_info.properties["uniqueid"],
            "name": discovery_info.properties["name"],
            "devicetype": discovery_info.properties["devicetype"],
        }

        return await self.async_step_check(entry_info)

    async def async_step_check(self, entry_info: dict) -> FlowResult:
        """Perform some checks and create entry if OK."""

        await self.async_set_unique_id(entry_info["unique_id"])
        self._abort_if_unique_id_configured(updates=entry_info)

        self.context["host"] = entry_info["host"]
        self.context["unique_id"] = entry_info["unique_id"]
        self.context["port"] = entry_info["port"]
        self.context["name"] = entry_info["name"]
        self.context["path"] = entry_info["path"]
        self.context["access_token"] = entry_info.get("access_token")
        self.context["registration_id"] = entry_info.get("registration_id")

        self.context["title_placeholders"] = {"name": self.context["name"]}

        async with await async_get_aiohuesyncbox_from_entry_data(entry_info) as api:
            if await api.is_registered():
                return await self._async_create_entry_from_context()

        return await self.async_step_link()

    async def _async_create_entry_from_context(self):
        """Return create entry with data from context."""
        entry_data = {
            "host": self.context["host"],
            "name": self.context["name"],
            "path": self.context["path"],
            "port": self.context["port"],
            "unique_id": self.context["unique_id"],
            "access_token": self.context["access_token"],
            "registration_id": self.context["registration_id"],
        }

        LOGGER.debug(
            "%s _async_create_entry_from_context\nentry_data:\n%s\n",
            __name__,
            textwrap.indent(log_entry_data(entry_data), "  "),
        )

        return self.async_create_entry(
            title=entry_data["name"],
            data=entry_data,
        )
