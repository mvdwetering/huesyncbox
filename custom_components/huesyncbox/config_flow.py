"""Config flow for Philips Hue Play HDMI Sync Box integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol  # type: ignore

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import CONF_IP_ADDRESS, CONF_UNIQUE_ID

import aiohuesyncbox

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_UNIQUE_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    async with aiohuesyncbox.HueSyncBox(
        data[CONF_IP_ADDRESS], data[CONF_UNIQUE_ID], data.get("access_token")
    ) as huesyncbox:
        try:
            # if not await huesyncbox.is_registered():
            #     raise InvalidAuth
            await huesyncbox.initialize()
            # data = {
            #     "host": data[CONF_IP_ADDRESS],
            #     "name": huesyncbox.device.name,
            #     "path": huesyncbox._path,
            #     "port": huesyncbox._port,
            #     "unique_id": huesyncbox.device.unique_id,
            #     "access_token": huesyncbox.access_token,
            # }
        except aiohuesyncbox.Unauthorized:
            raise InvalidAuth
        except aiohuesyncbox.RequestError:
            raise CannotConnect

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Name of the device"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Philips Hue Play HDMI Sync Box."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
