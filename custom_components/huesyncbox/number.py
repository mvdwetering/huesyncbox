from dataclasses import dataclass
from typing import Callable, Coroutine

import aiohuesyncbox

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HueSyncBoxCoordinator
from .helpers import BrightnessRangeConverter, stop_sync_and_retry_on_invalid_state


@dataclass
class HueSyncBoxNumberEntityDescription(NumberEntityDescription):
    get_value: Callable[[aiohuesyncbox.HueSyncBox], float] = None  # type: ignore[assignment]
    set_value_fn: Callable[[aiohuesyncbox.HueSyncBox, float], Coroutine] = None  # type: ignore[assignment]


async def set_brightness(api: aiohuesyncbox.HueSyncBox, brightness):
    await api.execution.set_state(
        brightness=BrightnessRangeConverter.ha_to_api(brightness)
    )


ENTITY_DESCRIPTIONS = [
    HueSyncBoxNumberEntityDescription(  # type: ignore
        key="brightness",  # type: ignore
        icon="mdi:brightness-5",  # type: ignore
        native_max_value=100,  # type: ignore
        native_min_value=1,  # type: ignore
        native_step=1,  # type: ignore
        native_unit_of_measurement="%",  # type: ignore
        get_value=lambda api: BrightnessRangeConverter.api_to_ha(
            api.execution.brightness
        ),
        set_value_fn=set_brightness,
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[NumberEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        if entity_description.get_value(coordinator.api) is not None:
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
        await stop_sync_and_retry_on_invalid_state(
            self.entity_description.set_value_fn, self.coordinator.api, value
        )
        await self.coordinator.async_request_refresh()
