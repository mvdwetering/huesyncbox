"""The Philips Hue Play HDMI Sync Box integration services."""

from typing import TYPE_CHECKING, Any

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, device_registry as dr
import probatio

import aiohuesyncbox

from .const import (
    ATTR_BRIDGE_CLIENTKEY,
    ATTR_BRIDGE_ID,
    ATTR_BRIDGE_USERNAME,
    ATTR_DEVICE_ID,
    ATTR_ENTERTAINMENT_AREA,
    ATTR_INPUT,
    ATTR_INTENSITY,
    ATTR_MODE,
    ATTR_POWER,
    ATTR_SYNC,
    DOMAIN,
    INPUTS,
    INTENSITIES,
    LOGGER,
    SERVICE_SET_BRIDGE,
    SERVICE_SET_SYNC_STATE,
    SYNC_MODES,
)
from .helpers import (
    BrightnessRangeConverter,
    get_group_from_area_name,
    get_hue_target_from_id,
    stop_sync_and_retry_on_invalid_state,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant, ServiceCall

HUESYNCBOX_SET_BRIDGE_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_DEVICE_ID): cv.string,
        probatio.Required(ATTR_BRIDGE_ID): cv.string,
        probatio.Required(ATTR_BRIDGE_USERNAME): cv.string,
        probatio.Required(ATTR_BRIDGE_CLIENTKEY): cv.string,
    }
)

HUESYNCBOX_SET_SYNC_STATE_SCHEMA = probatio.Schema(
    {
        probatio.Required(ATTR_DEVICE_ID): cv.string,
        probatio.Optional(ATTR_POWER): cv.boolean,
        probatio.Optional(ATTR_SYNC): cv.boolean,
        probatio.Optional(ATTR_BRIGHTNESS): probatio.All(
            probatio.Coerce(float), probatio.Range(min=1, max=100)
        ),
        probatio.Optional(ATTR_MODE): probatio.In(SYNC_MODES),
        probatio.Optional(ATTR_INTENSITY): probatio.In(INTENSITIES),
        probatio.Optional(ATTR_INPUT): probatio.In(INPUTS),
        probatio.Optional(ATTR_ENTERTAINMENT_AREA): cv.string,
    }
)


def syncbox_config_entry_for_device_id(
    hass: HomeAssistant, device_id: str
) -> ConfigEntry:
    device_registry = dr.async_get(hass)

    if device_entry := device_registry.async_get(device_id):
        # Since Home Assistant 2026.8 a device belongs to a single config entry.
        entry = hass.config_entries.async_get_entry(device_entry.config_entry_id)
        if entry is not None and entry.domain == DOMAIN:
            return entry

    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="invalid_device_id",
        translation_placeholders={"device_id": device_id},
    )


async def async_register_set_bridge_service(hass: HomeAssistant) -> None:
    async def async_set_bridge(call: ServiceCall) -> None:
        """Set bridge for the syncbox, note that this change is not instant.

        After calling it will take a while until the `bridge_unique_id` matches the new bridge id.
        When the bridge_connection_state is `connected`, `invalidgroup`, `streaming` or `busy` it is done, other status means it is connecting.
        The bridge change seems to take around 15 seconds.
        """
        config_entry = syncbox_config_entry_for_device_id(
            hass, call.data[ATTR_DEVICE_ID]
        )
        bridge_id = call.data.get(ATTR_BRIDGE_ID)
        username = call.data.get(ATTR_BRIDGE_USERNAME)
        clientkey = call.data.get(ATTR_BRIDGE_CLIENTKEY)

        await config_entry.runtime_data.coordinator.api.hue.set_bridge(
            bridge_id, username, clientkey
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BRIDGE,
        async_set_bridge,
        schema=HUESYNCBOX_SET_BRIDGE_SCHEMA,
    )


async def async_register_set_sync_state_service(hass: HomeAssistant) -> None:
    async def async_set_sync_state(call: ServiceCall) -> None:
        """Set sync state, allows combining of all options."""
        config_entry = syncbox_config_entry_for_device_id(
            hass, call.data[ATTR_DEVICE_ID]
        )
        coordinator = config_entry.runtime_data.coordinator

        target_sync_state = call.data

        # Resolve entertainment area
        group = get_group_from_area_name(
            coordinator.api, target_sync_state.get(ATTR_ENTERTAINMENT_AREA, "")
        )
        hue_target = get_hue_target_from_id(group.id) if group else None

        state = {
            "hdmi_active": target_sync_state.get(ATTR_POWER, None),
            "sync_active": target_sync_state.get(ATTR_SYNC, None),
            "mode": (
                aiohuesyncbox.ExecutionMode(target_sync_state[ATTR_MODE])
                if ATTR_MODE in target_sync_state
                else None
            ),
            "hdmi_source": (
                aiohuesyncbox.HdmiSource(target_sync_state[ATTR_INPUT])
                if ATTR_INPUT in target_sync_state
                else None
            ),
            "brightness": (
                BrightnessRangeConverter.ha_to_api(target_sync_state[ATTR_BRIGHTNESS])
                if ATTR_BRIGHTNESS in target_sync_state
                else None
            ),
            "intensity": (
                aiohuesyncbox.Intensity(target_sync_state[ATTR_INTENSITY])
                if ATTR_INTENSITY in target_sync_state
                else None
            ),
            "hue_target": hue_target,
        }

        async def set_state(api: aiohuesyncbox.HueSyncBox, **kwargs: Any) -> None:
            await api.execution.set_state(**kwargs)  # type: ignore  # noqa: PGH003

        try:
            await stop_sync_and_retry_on_invalid_state(
                set_state, coordinator.api, **state
            )
        except aiohuesyncbox.RequestError as ex:
            if "13: Invalid Key" in ex.args[0]:
                # Clarify this specific case as people will run into it
                LOGGER.warning(
                    "The service call resulted in an empty message to the syncbox. Make sure some data is provided."
                )
            else:
                raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SYNC_STATE,
        async_set_sync_state,
        schema=HUESYNCBOX_SET_SYNC_STATE_SCHEMA,
    )


async def async_register_services(hass: HomeAssistant) -> None:
    """Register services for the Hue Sync Box integration."""
    await async_register_set_bridge_service(hass)
    await async_register_set_sync_state_service(hass)
