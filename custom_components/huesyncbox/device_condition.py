"""Provide the device conditions for Philips Hue Play HDMI Sync Box."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import condition, config_validation as cv, entity_registry
from homeassistant.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

HDMI1_STATUS_LINKED = "hdmi1_status_linked"
HDMI2_STATUS_LINKED = "hdmi2_status_linked"
HDMI3_STATUS_LINKED = "hdmi3_status_linked"
HDMI4_STATUS_LINKED = "hdmi4_status_linked"

CONDITION_TYPES = {
    HDMI1_STATUS_LINKED,
    HDMI2_STATUS_LINKED,
    HDMI3_STATUS_LINKED,
    HDMI4_STATUS_LINKED,
}

CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
    }
)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for Philips Hue Play HDMI Sync Box devices."""
    registry = await entity_registry.async_get_registry(hass)
    conditions = []

    # Get all the integrations entities for this device
    for entry in entity_registry.async_entries_for_device(registry, device_id):
        # 1 Mediaplayer per device, no additional checks needed for now

        # Add conditions for each entity that belongs to this integration
        base_condition = {
            CONF_CONDITION: "device",
            CONF_DEVICE_ID: device_id,
            CONF_DOMAIN: DOMAIN,
            CONF_ENTITY_ID: entry.entity_id,
        }

        conditions += [{**base_condition, CONF_TYPE: cond} for cond in CONDITION_TYPES]

    return conditions


@callback
def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    if config_validation:
        config = CONDITION_SCHEMA(config)

    @callback
    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(
            hass,
            config[ATTR_ENTITY_ID],
            "linked",
            attribute=config[CONF_TYPE][
                : -len("_linked")
            ],  # Condition names are attribute + _linked. Bit hacky, TODO: replace with removesuffix in Python 3.9
        )

    return test_is_state
