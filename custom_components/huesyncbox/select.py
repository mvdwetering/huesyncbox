from dataclasses import dataclass
from typing import Callable,Coroutine

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from custom_components.huesyncbox.coordinator import HueSyncBoxCoordinator

from .const import DOMAIN, LOGGER

import aiohuesyncbox

@dataclass
class HueSyncBoxSelectEntityDescription(SelectEntityDescription):
    options_fn: Callable[[aiohuesyncbox.HueSyncBox], list[str]] = lambda x: []
    current_option_fn: Callable[[aiohuesyncbox.HueSyncBox], str] = lambda x: ""
    select_option_fn: Callable[[aiohuesyncbox.HueSyncBox, str], Coroutine] = None # type: ignore


class NO_INPUT:
    name: None

def get_hue_target_from_id(id_: str):
    """Determine API target from id"""
    try:
        return f"groups/{int(id_)}"
    except ValueError:
        return id_    

def available_inputs(api:aiohuesyncbox.HueSyncBox):
    return sorted(map(lambda input_: input_.name, api.hdmi.inputs))

def current_input(api:aiohuesyncbox.HueSyncBox):
    return next(filter(lambda x: x.id == api.execution.hdmi_source, api.hdmi.inputs), NO_INPUT).name

async def select_input(api:aiohuesyncbox.HueSyncBox, input_name):
    # Source is the user given name, so needs to be mapped back to a valid API value."""
    input_ = next(filter(lambda i: i.name == input_name, api.hdmi.inputs), None)
    if input_:
        await api.execution.set_state(hdmi_source=input_.id)


def available_entertainment_areas(api:aiohuesyncbox.HueSyncBox):
    return sorted(map(lambda group: group.name, api.hue.groups))

def current_entertainment_area(api:aiohuesyncbox.HueSyncBox):
    hue_target = (
        api.execution.hue_target
    )  # this is a string like "groups/123" or a UUID
    id_ = hue_target.replace("groups/", "")

    selected_area = None

    for group in api.hue.groups:
        if group.id == id_:
            selected_area = group.name
            break

    return selected_area

async def select_entertainment_area(api:aiohuesyncbox.HueSyncBox, name):
    # Source is the user given name, so needs to be mapped back to a valid API value."""
    group = next(filter(lambda g: g.name == name, api.hue.groups), None)
    if group:
        await api.execution.set_state(
            hue_target=get_hue_target_from_id(group.id)
        )        


ENTITY_DESCRIPTIONS = [
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="hdmi_input",  # type: ignore
        icon="mdi:hdmi-port",  # type: ignore
        options_fn=available_inputs,
        current_option_fn=current_input,
        select_option_fn=select_input,
    ),
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="entertainment_area",  # type: ignore
        icon="mdi:lamps",  # type: ignore
        entity_category=EntityCategory.CONFIG,  # type: ignore
        options_fn=available_entertainment_areas,
        current_option_fn=current_entertainment_area,
        select_option_fn=select_entertainment_area,
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

