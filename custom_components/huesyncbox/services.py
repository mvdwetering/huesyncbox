"""The Philips Hue Play HDMI Sync Box integration."""
import aiohuesyncbox
import voluptuous as vol  # type: ignore

from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import async_extract_config_entry_ids

from .const import (
    ATTR_BRIDGE_CLIENTKEY,
    ATTR_BRIDGE_ID,
    ATTR_BRIDGE_USERNAME,
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


HUESYNCBOX_SET_BRIDGE_SCHEMA = make_entity_service_schema(
    {
        vol.Required(ATTR_BRIDGE_ID): cv.string,
        vol.Required(ATTR_BRIDGE_USERNAME): cv.string,
        vol.Required(ATTR_BRIDGE_CLIENTKEY): cv.string,
    }
)

HUESYNCBOX_SET_SYNC_STATE_SCHEMA = make_entity_service_schema(
    {
        vol.Optional(ATTR_POWER): cv.boolean,
        vol.Optional(ATTR_SYNC): cv.boolean,
        vol.Optional(ATTR_BRIGHTNESS): vol.All(
            vol.Coerce(float), vol.Range(min=1, max=100)
        ),
        vol.Optional(ATTR_MODE): vol.In(SYNC_MODES),
        vol.Optional(ATTR_INTENSITY): vol.In(INTENSITIES),
        vol.Optional(ATTR_INPUT): vol.In(INPUTS),
        vol.Optional(ATTR_ENTERTAINMENT_AREA): cv.string,
    }
)


async def async_register_services(hass: HomeAssistant):

    async def async_set_bridge(call):
        """
        Set bridge, note that this change is not instant.
        After calling you will have to wait until the `bridge_unique_id` matches the new bridge id
        and the bridge_connection_state is `connected`, `invalidgroup`, `streaming` or `busy`, other status means it is connecting.
        I have seen the bridge change to take around 15 seconds.
        """

        config_entry_ids = await async_extract_config_entry_ids(hass, call)
        for config_entry_id in config_entry_ids:
            # Need to check if it is our config entry since async_extract_config_entry_ids
            # can return config entries from other integrations also
            # (e.g. area id or devices with entities from multiple integrations)
            if coordinator := hass.data[DOMAIN].get(config_entry_id):
                bridge_id = call.data.get(ATTR_BRIDGE_ID)
                username = call.data.get(ATTR_BRIDGE_USERNAME)
                clientkey = call.data.get(ATTR_BRIDGE_CLIENTKEY)

                await coordinator.api.hue.set_bridge(bridge_id, username, clientkey)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_BRIDGE,
        async_set_bridge,
        schema=HUESYNCBOX_SET_BRIDGE_SCHEMA,
    )

    async def async_set_sync_state(call):
        """Set sync state, allow combining of all options."""

        config_entry_ids = await async_extract_config_entry_ids(hass, call)
        for config_entry_id in config_entry_ids:
            # Need to check if it is our config entry since async_extract_config_entry_ids
            # can return config entries from other integrations also
            # (e.g. area id or devices with entities from multiple integrations)
            if coordinator := hass.data[DOMAIN].get(config_entry_id):
                sync_state = call.data

                # Resolve entertainment area
                group = get_group_from_area_name(
                    coordinator.api, sync_state.get(ATTR_ENTERTAINMENT_AREA, None)
                )
                hue_target = get_hue_target_from_id(group.id) if group else None

                state = {
                    "hdmi_active": sync_state.get(ATTR_POWER, None),
                    "sync_active": sync_state.get(ATTR_SYNC, None),
                    "mode": sync_state.get(ATTR_MODE, None),
                    "hdmi_source": sync_state.get(ATTR_INPUT, None),
                    "brightness": BrightnessRangeConverter.ha_to_api(
                        sync_state[ATTR_BRIGHTNESS]
                    )
                    if ATTR_BRIGHTNESS in sync_state
                    else None,
                    "intensity": sync_state.get(ATTR_INTENSITY, None),
                    "hue_target": hue_target,
                }

                async def set_state(api: aiohuesyncbox.HueSyncBox, **kwargs):
                    await api.execution.set_state(**kwargs)

                try:
                    await stop_sync_and_retry_on_invalid_state(
                        set_state, coordinator.api, **state
                    )
                except aiohuesyncbox.RequestError as ex:
                    if "13: Invalid Key" in ex.args[0]:
                        # Clarify this specific case as people will run into it
                        LOGGER.warning(
                            "The service call resulted in an empty message to the syncbox. Make sure some data is provided)."
                        )
                    else:
                        raise

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SYNC_STATE,
        async_set_sync_state,
        schema=HUESYNCBOX_SET_SYNC_STATE_SCHEMA,
    )
