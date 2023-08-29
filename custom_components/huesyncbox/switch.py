from dataclasses import dataclass
from typing import Any, Callable, Coroutine

import aiohuesyncbox

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.helpers.entity import EntityCategory, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HueSyncBoxCoordinator
from .helpers import stop_sync_and_retry_on_invalid_state


@dataclass
class HueSyncBoxSwitchEntityDescription(SwitchEntityDescription):
    is_on: Callable[[aiohuesyncbox.HueSyncBox], bool] = None  # type: ignore[assignment]
    turn_on: Callable[[aiohuesyncbox.HueSyncBox], Coroutine] = None  # type: ignore[assignment]
    turn_off: Callable[[aiohuesyncbox.HueSyncBox], Coroutine] = None  # type: ignore[assignment]
    is_supported: Callable[[aiohuesyncbox.HueSyncBox], bool] = lambda _: True


ENTITY_DESCRIPTIONS = [
    HueSyncBoxSwitchEntityDescription(  # type: ignore
        key="power",  # type: ignore
        icon="mdi:power",  # type: ignore
        is_on=lambda api: api.execution.mode != "powersave",
        turn_on=lambda api: api.execution.set_state(mode="passthrough"),
        turn_off=lambda api: api.execution.set_state(mode="powersave"),
    ),
    HueSyncBoxSwitchEntityDescription(  # type: ignore
        key="light_sync",  # type: ignore
        icon="mdi:television-ambient-light",  # type: ignore
        is_on=lambda api: api.execution.mode not in ["powersave", "passthrough"],
        turn_on=lambda api: api.execution.set_state(sync_active=True),
        turn_off=lambda api: api.execution.set_state(sync_active=False),
    ),
    HueSyncBoxSwitchEntityDescription(  # type: ignore
        key="dolby_vision_compatibility",  # type: ignore
        icon="mdi:hdr",  # type: ignore
        entity_category=EntityCategory.CONFIG,  # type: ignore
        is_on=lambda api: api.behavior.force_dovi_native == 1,
        turn_on=lambda api: api.behavior.set_force_dovi_native(1),
        turn_off=lambda api: api.behavior.set_force_dovi_native(0),
        is_supported=lambda api: api.behavior.force_dovi_native is not None,
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):

    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SwitchEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        if entity_description.is_supported(coordinator.api):
            entities.append(HueSyncBoxSwitch(coordinator, entity_description))

    async_add_entities(entities)


class HueSyncBoxSwitch(CoordinatorEntity, SwitchEntity):

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSwitchEntityDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.coordinator: HueSyncBoxCoordinator

        self.entity_description: HueSyncBoxSwitchEntityDescription = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{self.entity_description.key}_{self.coordinator.api.device.unique_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.device.unique_id)}
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        return self.entity_description.is_on(self.coordinator.api)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await stop_sync_and_retry_on_invalid_state(
            self.entity_description.turn_on, self.coordinator.api
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any):
        """Turn the entity off."""
        await stop_sync_and_retry_on_invalid_state(
            self.entity_description.turn_off, self.coordinator.api
        )
        await self.coordinator.async_request_refresh()
