"""The Philips Hue Play HDMI Sync Box integration."""
import aiohuesyncbox
import voluptuous as vol  # type: ignore

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_BRIGHTNESS_STEP
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
    ATTR_INPUT_NEXT,
    ATTR_INPUT_PREV,
    ATTR_INTENSITY,
    ATTR_INTENSITY_NEXT,
    ATTR_INTENSITY_PREV,
    ATTR_MODE,
    ATTR_MODE_NEXT,
    ATTR_MODE_PREV,
    ATTR_SYNC,
    ATTR_SYNC_TOGGLE,
    DOMAIN,
    INPUTS,
    INTENSITIES,
    LOGGER,
    SERVICE_SET_BRIDGE,
    SERVICE_SET_SYNC_STATE,
    SYNC_MODES,
)

from .helpers import (
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
        vol.Optional(ATTR_SYNC): cv.boolean,
        vol.Optional(ATTR_SYNC_TOGGLE): cv.boolean,
        vol.Optional(ATTR_BRIGHTNESS): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=100)
        ),
        vol.Optional(ATTR_BRIGHTNESS_STEP): vol.All(
            vol.Coerce(float), vol.Range(min=-100, max=100)
        ),
        vol.Optional(ATTR_MODE): vol.In(SYNC_MODES),
        vol.Optional(ATTR_MODE_NEXT): cv.boolean,
        vol.Optional(ATTR_MODE_PREV): cv.boolean,
        vol.Optional(ATTR_INTENSITY): vol.In(INTENSITIES),
        vol.Optional(ATTR_INTENSITY_NEXT): cv.boolean,
        vol.Optional(ATTR_INTENSITY_PREV): cv.boolean,
        vol.Optional(ATTR_INPUT): vol.In(INPUTS),
        vol.Optional(ATTR_INPUT_NEXT): cv.boolean,
        vol.Optional(ATTR_INPUT_PREV): cv.boolean,
        vol.Optional(ATTR_ENTERTAINMENT_AREA): cv.string,
    }
)


async def async_register_services(hass: HomeAssistant):
    async def async_set_bridge(call):
        """
        Set bridge, note that this change is not instant.
        After calling you will have to wait until the `bridge_unique_id` matches the new bridge id
        and the bridge_connection_state is `connected`, `invalidgroup` or `streaming`, other status means it is connecting.
        I have seen the bridge change to take around 15 seconds.
        """

        config_entry_ids = await async_extract_config_entry_ids(hass, call)
        for config_entry_id in config_entry_ids:
            coordinator = hass.data[DOMAIN][config_entry_id]

            bridge_id = call.data.get(ATTR_BRIDGE_ID)
            username = call.data.get(ATTR_BRIDGE_USERNAME)
            clientkey = call.data.get(ATTR_BRIDGE_CLIENTKEY)

            await coordinator.api.hue.set_bridge(bridge_id, username, clientkey)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BRIDGE):
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
            coordinator = hass.data[DOMAIN][config_entry_id]

            sync_state = call.data

            # Special handling for Toggle specific mode as that cannot be done in 1 call on the API
            sync_toggle = sync_state.get(ATTR_SYNC_TOGGLE, None)
            mode = sync_state.get(ATTR_MODE, None)
            if sync_toggle and mode:
                if coordinator.api.execution.mode != mode:
                    # When not syncing in the desired mode, just turn on the desired mode, no toggle
                    sync_toggle = None
                else:
                    # Otherwise just toggle, no mode (setting mode would interfere with the toggle)
                    mode = None

            # Entertainment area
            group = get_group_from_area_name(
                coordinator.api, sync_state.get(ATTR_ENTERTAINMENT_AREA, None)
            )
            hue_target = get_hue_target_from_id(group.id) if group else None

            state = {
                "sync_active": sync_state.get(ATTR_SYNC, None),
                "sync_toggle": sync_toggle,
                "mode": mode,
                "mode_cycle": "next"
                if ATTR_MODE_NEXT in sync_state
                else "previous"
                if ATTR_MODE_PREV in sync_state
                else None,
                "hdmi_source": sync_state.get(ATTR_INPUT, None),
                "hdmi_source_cycle": "next"
                if ATTR_INPUT_NEXT in sync_state
                else "previous"
                if ATTR_INPUT_PREV in sync_state
                else None,
                "brightness": int(sync_state[ATTR_BRIGHTNESS] * 2)
                if ATTR_BRIGHTNESS in sync_state
                else None,
                "brightness_step": int(sync_state[ATTR_BRIGHTNESS_STEP] * 2)
                if ATTR_BRIGHTNESS_STEP in sync_state
                else None,
                "intensity": sync_state.get(ATTR_INTENSITY, None),
                "intensity_cycle": "next"
                if ATTR_INTENSITY_NEXT in sync_state
                else "previous"
                if ATTR_INTENSITY_PREV in sync_state
                else None,
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
                    # Use a warning so it is visually separated from the actual error
                    LOGGER.warning(
                        "This error most likely occured because the service call resulted in an empty message to the syncbox. Make sure that the selected options would result in an action on the syncbox (e.g. requesting only `sync_toggle:false` would cause such an error)."
                    )
                raise

    if not hass.services.has_service(DOMAIN, SERVICE_SET_SYNC_STATE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_SYNC_STATE,
            async_set_sync_state,
            schema=HUESYNCBOX_SET_SYNC_STATE_SCHEMA,
        )


async def async_unregister_services(hass: HomeAssistant):
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIDGE)
    hass.services.async_remove(DOMAIN, SERVICE_SET_SYNC_STATE)
