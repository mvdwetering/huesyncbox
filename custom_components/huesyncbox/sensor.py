from dataclasses import dataclass
from typing import Callable

import aiohuesyncbox

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HueSyncBoxCoordinator
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class HueSyncBoxSensorEntityDescription(SensorEntityDescription):
    get_value: Callable[[aiohuesyncbox.HueSyncBox], str] = None  # type: ignore[assignment]


WIFI_STRENGTH_STATES = {
    0: "not_connected",
    1: "weak",
    2: "fair",
    3: "good",
    4: "excellent",
}

ENTITY_DESCRIPTIONS = [
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="bridge_connection_state",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=[
            "uninitialized",
            "disconnected",
            "connecting",
            "unauthorized",
            "connected",
            "invalidgroup",
            "streaming",
            "busy",
        ],  # type: ignore
        get_value=lambda api: api.hue.connection_state,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="bridge_unique_id",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: api.hue.bridge_unique_id,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi1_status",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.input1.status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi2_status",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.input2.status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi3_status",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.input3.status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi4_status",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.input4.status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="ip_address",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: api.device.ip_address,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="wifi_strength",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: WIFI_STRENGTH_STATES[api.device.wifi.strength],  # type: ignore
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="content_info",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: api.hdmi.content_specs,  # type: ignore
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = config_entry.runtime_data.coordinator

    entities: list[SensorEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        try:
            if entity_description.get_value(coordinator.api) is not None:
                entities.append(HueSyncBoxSensor(coordinator, entity_description))
        except:
            # When not able to read value, entity is not supported
            pass

    async_add_entities(entities)


class HueSyncBoxSensor(CoordinatorEntity, SensorEntity):
    """Representation of a HueSyncBox sensor"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSensorEntityDescription,
    ):
        super().__init__(coordinator)  # Pass coordinator to CoordinatorEntity
        self.coordinator: HueSyncBoxCoordinator

        self.entity_description: HueSyncBoxSensorEntityDescription = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{self.entity_description.key}_{self.coordinator.api.device.unique_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.device.unique_id)}
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.entity_description.get_value(self.coordinator.api)
