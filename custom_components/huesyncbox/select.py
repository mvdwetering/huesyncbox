from dataclasses import dataclass
from typing import Callable, Coroutine

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import HueSyncBoxCoordinator
from .helpers import get_hue_target_from_id, stop_sync_and_retry_on_invalid_state

from .const import (
    DOMAIN,
    INTENSITIES,
    SYNC_MODES,
)

import aiohuesyncbox


LED_INDICATOR_MODES = ["off", "normal", "dimmed"]
INPUTS = ["input1", "input2", "input3", "input4"]


@dataclass(frozen=True, kw_only=True)
class HueSyncBoxSelectEntityDescription(SelectEntityDescription):
    options_fn: Callable[[aiohuesyncbox.HueSyncBox], list[str]] | None = None
    current_option_fn: Callable[[aiohuesyncbox.HueSyncBox], str] = None  # type: ignore[assignment]
    select_option_fn: Callable[[aiohuesyncbox.HueSyncBox, str], Coroutine] = None  # type: ignore[assignment]


class NO_INPUT:
    name: None


def get_sync_mode(api: aiohuesyncbox.HueSyncBox):
    """Get mode"""
    mode = api.execution.mode
    if not api.execution.mode in SYNC_MODES:
        mode = api.execution.last_sync_mode
    return mode


def available_inputs(api: aiohuesyncbox.HueSyncBox):
    inputs = []
    for input_id in INPUTS:
        input = getattr(api.hdmi, input_id)
        inputs.append(input.name)
    return inputs


def current_input(api: aiohuesyncbox.HueSyncBox):
    for input_id in INPUTS:
        if input_id == api.execution.hdmi_source:
            return getattr(api.hdmi, input_id).name


async def select_input(api: aiohuesyncbox.HueSyncBox, input_name):
    # Inputname is the user given name, so needs to be mapped back to a valid API value."""
    for input_id in INPUTS:
        input = getattr(api.hdmi, input_id)
        if input_name == input.name:
            await api.execution.set_state(hdmi_source=input_id)


def available_entertainment_areas(api: aiohuesyncbox.HueSyncBox):
    return sorted(map(lambda group: group.name, api.hue.groups))


def current_entertainment_area(api: aiohuesyncbox.HueSyncBox):
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


async def select_entertainment_area(api: aiohuesyncbox.HueSyncBox, name):
    # Source is the user given name, so needs to be mapped back to a valid API value."""
    group = next(filter(lambda g: g.name == name, api.hue.groups), None)
    if group:
        await api.execution.set_state(hue_target=get_hue_target_from_id(group.id))


def current_intensity(api: aiohuesyncbox.HueSyncBox):
    sync_mode = get_sync_mode(api)
    return getattr(api.execution, sync_mode).intensity


async def select_intensity(api: aiohuesyncbox.HueSyncBox, intensity):
    """Set intensity for sync mode."""
    sync_mode = get_sync_mode(api)

    # Intensity is per mode so update accordingly
    state = {sync_mode: {"intensity": intensity}}
    await api.execution.set_state(**state)  # type: ignore


def current_sync_mode(api: aiohuesyncbox.HueSyncBox):
    return get_sync_mode(api)


async def select_sync_mode(api: aiohuesyncbox.HueSyncBox, sync_mode):
    """Set sync mode."""
    await api.execution.set_state(mode=sync_mode)


def current_led_indicator_mode(api: aiohuesyncbox.HueSyncBox):
    return LED_INDICATOR_MODES[api.device.led_mode]


async def select_led_indicator_mode(api: aiohuesyncbox.HueSyncBox, mode):
    """Set led indicator mode."""
    await api.device.set_led_mode(LED_INDICATOR_MODES.index(mode))


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
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="intensity",  # type: ignore
        icon="mdi:sine-wave",  # type: ignore
        options=INTENSITIES,  # type: ignore
        current_option_fn=current_intensity,
        select_option_fn=select_intensity,
    ),
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="sync_mode",  # type: ignore
        options=SYNC_MODES,  # type: ignore
        current_option_fn=current_sync_mode,
        select_option_fn=select_sync_mode,
    ),
    HueSyncBoxSelectEntityDescription(  # type: ignore
        key="led_indicator_mode",  # type: ignore
        icon="mdi:alarm-light",  # type: ignore
        entity_category=EntityCategory.CONFIG,  # type: ignore
        options=sorted(LED_INDICATOR_MODES),  # type: ignore
        current_option_fn=current_led_indicator_mode,
        select_option_fn=select_led_indicator_mode,
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
        if self.entity_description.options_fn is not None:
            return self.entity_description.options_fn(self.coordinator.api)
        return super().options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await stop_sync_and_retry_on_invalid_state(
            self.entity_description.select_option_fn, self.coordinator.api, option
        )
        await self.coordinator.async_request_refresh()
