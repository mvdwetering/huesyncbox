from dataclasses import dataclass
from typing import Callable,Coroutine

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from custom_components.huesyncbox.coordinator import HueSyncBoxCoordinator

from .const import DOMAIN

import aiohuesyncbox

@dataclass
class HueSyncBoxSelectEntityDescription(SelectEntityDescription):
    options_fn: Callable[[aiohuesyncbox.HueSyncBox], list[str]] = lambda x: []
    current_option_fn: Callable[[aiohuesyncbox.HueSyncBox], str] = lambda x: ""
    select_option_fn: Callable[[aiohuesyncbox.HueSyncBox, str], Coroutine] = None # type: ignore


class NO_INPUT:
    name: None

def current_input(api:aiohuesyncbox.HueSyncBox):
    return next(filter(lambda x: x.id == api.execution.hdmi_source, api.hdmi.inputs), NO_INPUT).name

def available_inputs(api:aiohuesyncbox.HueSyncBox):
    return sorted(map(lambda input_: input_.name, api.hdmi.inputs))

async def select_input(api:aiohuesyncbox.HueSyncBox, input_name):
    # Source is the user given name, so needs to be mapped back to a valid API value."""
    input_ = next(filter(lambda i: i.name == input_name, api.hdmi.inputs), None)
    if input_:
        await api.execution.set_state(hdmi_source=input_.id)


ENTITY_DESCRIPTIONS = [
    # Suppress following mypy message, which seems to be not an issue as other values have defaults:
    # custom_components/yamaha_ynca/number.py:19: error: Missing positional arguments "entity_registry_enabled_default", "entity_registry_visible_default", "force_update", "icon", "has_entity_name", "unit_of_measurement", "max_value", "min_value", "step" in call to "NumberEntityDescription"  [call-arg]
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="hdmi_input",  # type: ignore
        icon="mdi:hdmi-port",  # type: ignore
        options_fn=available_inputs,
        current_option_fn=current_input,
        select_option_fn=select_input,
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):

    coordinator: HueSyncBoxCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[SelectEntity] = []

    for entity_description in ENTITY_DESCRIPTIONS:
        entities.append(HueSyncBoxSelect(coordinator, entity_description))

    async_add_entities(entities)


class HueSyncBoxSelect(CoordinatorEntity, SelectEntity):
    """Representation of a select entity on a Yamaha Ynca device."""

    entity_description: HueSyncBoxSelectEntityDescription

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSelectEntityDescription,
    ):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.coordinator: HueSyncBoxCoordinator

        self.entity_description = entity_description
        self._attr_translation_key = self.entity_description.key

        self._attr_unique_id = (
            f"{self.entity_description.key}_{self.coordinator.api.device.unique_id}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.api.device.unique_id)}
        )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.current_option_fn(self.coordinator.api)

    @property
    def options(self) -> list[str]:
        return self.entity_description.options_fn(self.coordinator.api)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_option_fn(self.coordinator.api, option)

