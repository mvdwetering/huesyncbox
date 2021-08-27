"""Provides device triggers for Philips Hue Play HDMI Sync Box."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.automation import AutomationActionType
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
    CONF_ATTRIBUTE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, entity_registry
from homeassistant.helpers.typing import ConfigType

from . import DOMAIN

HDMI1_STATUS_CHANGED = "hdmi1_status_changed"
HDMI2_STATUS_CHANGED = "hdmi2_status_changed"
HDMI3_STATUS_CHANGED = "hdmi3_status_changed"
HDMI4_STATUS_CHANGED = "hdmi4_status_changed"

TRIGGER_TYPES = {
    HDMI1_STATUS_CHANGED,
    HDMI2_STATUS_CHANGED,
    HDMI3_STATUS_CHANGED,
    HDMI4_STATUS_CHANGED,
}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)


async def async_get_triggers(hass: HomeAssistant, device_id: str) -> list[dict]:
    """List device triggers for Philips Hue Play HDMI Sync Box devices."""
    registry = await entity_registry.async_get_registry(hass)
    triggers = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        # 1 Mediaplayer per device, no additional checks needed for now

        # Add triggers for each entity that belongs to this integration
        base_trigger = {
            CONF_PLATFORM: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.entity_id,
        }
        triggers.append({**base_trigger, CONF_TYPE: HDMI1_STATUS_CHANGED})
        triggers.append({**base_trigger, CONF_TYPE: HDMI2_STATUS_CHANGED})
        triggers.append({**base_trigger, CONF_TYPE: HDMI3_STATUS_CHANGED})
        triggers.append({**base_trigger, CONF_TYPE: HDMI4_STATUS_CHANGED})

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    state_config = {
        state.CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        CONF_ATTRIBUTE: config[CONF_TYPE][
            : -len("_changed")
        ],  # Trigger names are attribute + _changed. Bit hacky, TODO: replace with removesuffix in Python 3.9
    }
    state_config = state.TRIGGER_SCHEMA(state_config)
    return await state.async_attach_trigger(
        hass, state_config, action, automation_info, platform_type="device"
    )
