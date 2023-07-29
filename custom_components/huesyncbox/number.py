from dataclasses import dataclass
from typing import Callable, Coroutine

import aiohuesyncbox

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HueSyncBoxCoordinator
from .const import DOMAIN


@dataclass
class HueSyncBoxNumberEntityDescription(NumberEntityDescription):
    get_value: Callable[[aiohuesyncbox.HueSyncBox], float] = lambda _: 0
    set_value_fn: Callable[[aiohuesyncbox.HueSyncBox, float], Coroutine] = None  # type: ignore


async def set_brightness(api: aiohuesyncbox.HueSyncBox, brightness):
    await api.execution.set_state(brightness=int(brightness * 2))


ENTITY_DESCRIPTIONS = [
    HueSyncBoxNumberEntityDescription(  # type: ignore
        key="brightness",  # type: ignore
        icon="mdi:brightness-5",  # type: ignore
        native_step=0.5,  # type: ignore
        get_value=lambda api: api.execution.brightness / 2,
        set_value_fn=set_brightness,
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[NumberEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        entities.append(HueSyncBoxNumber(coordinator, entity_description))

    async_add_entities(entities)


class HueSyncBoxNumber(CoordinatorEntity, NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxNumberEntityDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.coordinator: HueSyncBoxCoordinator

        self.entity_description: HueSyncBoxNumberEntityDescription = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{self.entity_description.key}_{self.coordinator.api.device.unique_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.device.unique_id)}
        )

    @property
    def native_value(self) -> float | None:
        return self.entity_description.get_value(self.coordinator.api)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_value_fn(self.coordinator.api, value)
