from collections.abc import Callable
import contextlib
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import aiohuesyncbox

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
    HueSyncBoxSensorEntityDescription(
        key="bridge_connection_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "uninitialized",
            "disconnected",
            "connecting",
            "unauthorized",
            "connected",
            "invalidgroup",
            "streaming",
            "busy",
        ],
        get_value=lambda api: api.hue.connection_state,
    ),
    HueSyncBoxSensorEntityDescription(
        key="bridge_unique_id",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        get_value=lambda api: api.hue.bridge_unique_id,
    ),
    HueSyncBoxSensorEntityDescription(
        key="hdmi1_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["unplugged", "plugged", "linked", "unknown"],
        get_value=lambda api: api.hdmi.input1.status,
    ),
    HueSyncBoxSensorEntityDescription(
        key="hdmi2_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["unplugged", "plugged", "linked", "unknown"],
        get_value=lambda api: api.hdmi.input2.status,
    ),
    HueSyncBoxSensorEntityDescription(
        key="hdmi3_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["unplugged", "plugged", "linked", "unknown"],
        get_value=lambda api: api.hdmi.input3.status,
    ),
    HueSyncBoxSensorEntityDescription(
        key="hdmi4_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=["unplugged", "plugged", "linked", "unknown"],
        get_value=lambda api: api.hdmi.input4.status,
    ),
    HueSyncBoxSensorEntityDescription(
        key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        get_value=lambda api: api.device.ip_address,
    ),
    HueSyncBoxSensorEntityDescription(
        key="wifi_strength",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        get_value=lambda api: WIFI_STRENGTH_STATES[api.device.wifi.strength],  # type: ignore[union-attr]
        device_class=SensorDeviceClass.ENUM,
        options=["not_connected", "weak", "fair", "good", "excellent"],
    ),
    HueSyncBoxSensorEntityDescription(
        key="content_info",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        get_value=lambda api: api.hdmi.content_specs,
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = config_entry.runtime_data.coordinator

    entities: list[SensorEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        # When not able to read value, entity is not supported
        with contextlib.suppress(Exception):
            if entity_description.get_value(coordinator.api) is not None:
                entities.append(HueSyncBoxSensor(coordinator, entity_description))

    async_add_entities(entities)


class HueSyncBoxSensor(CoordinatorEntity[HueSyncBoxCoordinator], SensorEntity):
    """Representation of a HueSyncBox sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)  # Pass coordinator to CoordinatorEntity

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
