from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HueSyncBoxCoordinator
from .helpers import BrightnessRangeConverter, stop_sync_and_retry_on_invalid_state

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    import aiohuesyncbox

    from . import HueSyncBoxConfigEntry


@dataclass(frozen=True, kw_only=True)
class HueSyncBoxNumberEntityDescription(NumberEntityDescription):
    get_value: Callable[[aiohuesyncbox.HueSyncBox], float | None]
    set_value_fn: Callable[[aiohuesyncbox.HueSyncBox, float], Coroutine]
    is_supported_fn: Callable[[aiohuesyncbox.HueSyncBox], bool] = lambda _: True

async def set_brightness(api: aiohuesyncbox.HueSyncBox, brightness: float) -> None:
    await api.execution.set_state(
        brightness=BrightnessRangeConverter.ha_to_api(brightness)
    )


ENTITY_DESCRIPTIONS = [
    HueSyncBoxNumberEntityDescription(
        key="brightness",
        native_max_value=100,
        native_min_value=1,
        native_step=1,
        native_unit_of_measurement="%",
        get_value=lambda api: BrightnessRangeConverter.api_to_ha(
            api.execution.brightness
        ),
        set_value_fn=set_brightness,
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: HueSyncBoxConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = config_entry.runtime_data.coordinator

    entities: list[NumberEntity] = [
        HueSyncBoxNumber(coordinator, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
        if entity_description.is_supported_fn(coordinator.api)
    ]

    async_add_entities(entities)


class HueSyncBoxNumber(CoordinatorEntity[HueSyncBoxCoordinator], NumberEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxNumberEntityDescription,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

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
