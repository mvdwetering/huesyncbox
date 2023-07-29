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


@dataclass
class HueSyncBoxSensorEntityDescription(SensorEntityDescription):
    get_value: Callable[[aiohuesyncbox.HueSyncBox], str] = lambda _: ""


ENTITY_DESCRIPTIONS = [
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="bridge_connection_state",  # type: ignore
        icon="mdi:connection",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["uninitialized", "disconnected", "connecting", "unauthorized", "connected", "invalidgroup", "streaming", "busy"],  # type: ignore
        get_value=lambda api: api.hue.connection_state,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="bridge_unique_id",  # type: ignore
        icon="mdi:bridge",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: api.hue.bridge_unique_id,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi1_status",  # type: ignore
        icon="mdi:video-input-hdmi",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.inputs[0].status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi2_status",  # type: ignore
        icon="mdi:video-input-hdmi",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.inputs[1].status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi3_status",  # type: ignore
        icon="mdi:video-input-hdmi",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.inputs[2].status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="hdmi4_status",  # type: ignore
        icon="mdi:video-input-hdmi",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        device_class=SensorDeviceClass.ENUM,  # type: ignore
        options=["unplugged", "plugged", "linked", "unknown"],  # type: ignore
        get_value=lambda api: api.hdmi.inputs[3].status,
    ),
    HueSyncBoxSensorEntityDescription(  # type: ignore
        key="ip_address",  # type: ignore
        icon="mdi:ip-network",  # type: ignore
        entity_category=EntityCategory.DIAGNOSTIC,  # type: ignore
        entity_registry_enabled_default=False,  # type: ignore
        get_value=lambda api: api.device.ip_address
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SensorEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        entities.append(HueSyncBoxSensor(coordinator, entity_description))

    async_add_entities(entities)


class HueSyncBoxSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSensorEntityDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
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
        return self.entity_description.get_value(self.coordinator.api)
