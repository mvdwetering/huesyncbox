"""Provides device automations for Philips Hue Play HDMI Sync Box."""
from typing import List, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import ATTR_BRIGHTNESS_STEP
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import entity_registry

from .const import (
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
    INPUT_HDMI1,
    INPUT_HDMI2,
    INPUT_HDMI3,
    INPUT_HDMI4,
    INTENSITY_HIGH,
    INTENSITY_INTENSE,
    INTENSITY_MODERATE,
    INTENSITY_SUBTLE,
    MODE_GAME,
    MODE_MUSIC,
    MODE_VIDEO,
    SERVICE_SET_INTENSITY,
    SERVICE_SET_SYNC_STATE,
)

SERVICE = "service"
SERVICE_DATA = "service_data"

# List of device actions is derived from the available actions for the Philips Hue Play HDMI Sync Box in the Logitech Harmony
ACTION_TYPES = {
    "brightness_decrease": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_BRIGHTNESS_STEP: -0.1},
    },
    "brightness_increase": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_BRIGHTNESS_STEP: 0.1},
    },
    "intensity_down": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INTENSITY_PREV: True},
    },
    "intensity_up": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INTENSITY_NEXT: True},
    },
    "intensity_subtle": {
        SERVICE: SERVICE_SET_INTENSITY,
        SERVICE_DATA: {ATTR_INTENSITY: INTENSITY_SUBTLE},
    },
    "intensity_moderate": {
        SERVICE: SERVICE_SET_INTENSITY,
        SERVICE_DATA: {ATTR_INTENSITY: INTENSITY_MODERATE},
    },
    "intensity_high": {
        SERVICE: SERVICE_SET_INTENSITY,
        SERVICE_DATA: {ATTR_INTENSITY: INTENSITY_HIGH},
    },
    "intensity_intense": {
        SERVICE: SERVICE_SET_INTENSITY,
        SERVICE_DATA: {ATTR_INTENSITY: INTENSITY_INTENSE},
    },
    "sync_toggle": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_SYNC_TOGGLE: True},
    },
    "sync_video_toggle": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_SYNC_TOGGLE: True, ATTR_MODE: MODE_VIDEO},
    },
    "sync_music_toggle": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_SYNC_TOGGLE: True, ATTR_MODE: MODE_MUSIC},
    },
    "sync_game_toggle": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_SYNC_TOGGLE: True, ATTR_MODE: MODE_GAME},
    },
    "sync_video_on": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_VIDEO},
    },
    "sync_music_on": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_MUSIC},
    },
    "sync_game_on": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_GAME},
    },
    "sync_on": {SERVICE: SERVICE_SET_SYNC_STATE, SERVICE_DATA: {ATTR_SYNC: True}},
    "sync_off": {SERVICE: SERVICE_SET_SYNC_STATE, SERVICE_DATA: {ATTR_SYNC: False}},
    "input_next": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT_NEXT: True},
    },
    "input_previous": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT_PREV: True},
    },
    "input_hdmi1": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT: INPUT_HDMI1},
    },
    "input_hdmi2": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT: INPUT_HDMI2},
    },
    "input_hdmi3": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT: INPUT_HDMI3},
    },
    "input_hdmi4": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_INPUT: INPUT_HDMI4},
    },
    "mode_next": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE_NEXT: True},
    },
    "mode_previous": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE_PREV: True},
    },
    "mode_game": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_GAME},
    },
    "mode_music": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_MUSIC},
    },
    "mode_video": {
        SERVICE: SERVICE_SET_SYNC_STATE,
        SERVICE_DATA: {ATTR_MODE: MODE_VIDEO},
    },
    "toggle": {CONF_DOMAIN: "media_player", SERVICE: SERVICE_TOGGLE},
    "turn_on": {CONF_DOMAIN: "media_player", SERVICE: SERVICE_TURN_ON},
    "turn_off": {CONF_DOMAIN: "media_player", SERVICE: SERVICE_TURN_OFF},
}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES.keys()),
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
    }
)


async def async_get_actions(hass: HomeAssistant, device_id: str) -> List[dict]:
    """List device actions for Philips Hue Play HDMI Sync Box devices."""

    actions = []

    # Get all the integrations entities for this device
    registry = await entity_registry.async_get_registry(hass)
    for entry in entity_registry.async_entries_for_device(registry, device_id):

        # 1 Mediaplayer per device, no additional checks needed for now
        for type_ in ACTION_TYPES.keys():
            actions.append(
                {
                    CONF_DEVICE_ID: device_id,
                    CONF_DOMAIN: DOMAIN,
                    CONF_ENTITY_ID: entry.entity_id,
                    CONF_TYPE: type_,
                }
            )

    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Optional[Context]
) -> None:

    """Execute a device action."""
    config = ACTION_SCHEMA(config)

    service = ACTION_TYPES[config[CONF_TYPE]][SERVICE]
    service_data = ACTION_TYPES[config[CONF_TYPE]].get(SERVICE_DATA, {})
    service_data[ATTR_ENTITY_ID] = config[CONF_ENTITY_ID]
    service_domain = ACTION_TYPES[config[CONF_TYPE]].get(CONF_DOMAIN, DOMAIN)

    await hass.services.async_call(
        service_domain, service, service_data, blocking=True, context=context
    )
