from collections.abc import Callable, Coroutine
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

import aiohuesyncbox

from .const import DOMAIN, INTENSITIES, SYNC_MODES
from .coordinator import HueSyncBoxCoordinator
from .helpers import get_hue_target_from_id, stop_sync_and_retry_on_invalid_state

LED_INDICATOR_MODES = ["off", "normal", "dimmed"]
INPUTS = ["input1", "input2", "input3", "input4"]


@dataclass(frozen=True, kw_only=True)
class HueSyncBoxSelectEntityDescription(SelectEntityDescription):
    options_fn: Callable[[aiohuesyncbox.HueSyncBox], list[str]] | None = None
    current_option_fn: Callable[[aiohuesyncbox.HueSyncBox], str] = None  # type: ignore[assignment]
    select_option_fn: Callable[[aiohuesyncbox.HueSyncBox, str], Coroutine] = None  # type: ignore[assignment]


class NO_INPUT:  # noqa: N801
    name: None


def get_sync_mode(api: aiohuesyncbox.HueSyncBox) -> str:
    """Get mode."""
    mode = api.execution.mode
    if api.execution.mode not in SYNC_MODES:
        mode = api.execution.last_sync_mode
    return mode


def available_inputs(api: aiohuesyncbox.HueSyncBox) -> list[str]:
    inputs = []
    for input_id in INPUTS:
        input_ = getattr(api.hdmi, input_id)
        inputs.append(input_.name)
    return inputs


def current_input(api: aiohuesyncbox.HueSyncBox) -> str:
    for input_id in INPUTS:
        if input_id == api.execution.hdmi_source:
            return getattr(api.hdmi, input_id).name
    return "no_input"


async def select_input(api: aiohuesyncbox.HueSyncBox, input_name: str) -> None:
    # Inputname is the user given name, so needs to be mapped back to a valid API value."""
    for input_id in INPUTS:
        input_ = getattr(api.hdmi, input_id)
        if input_name == input_.name:
            await api.execution.set_state(hdmi_source=input_id)


def available_entertainment_areas(api: aiohuesyncbox.HueSyncBox) -> list[str]:
    return sorted(group.name for group in api.hue.groups)


def current_entertainment_area(api: aiohuesyncbox.HueSyncBox) -> str:
    hue_target = (
        api.execution.hue_target
    )  # this is a string like "groups/123" or a UUID
    id_ = hue_target.replace("groups/", "")

    selected_area = "no_area"

    for group in api.hue.groups:
        if group.id == id_:
            selected_area = group.name
            break

    return selected_area


async def select_entertainment_area(api: aiohuesyncbox.HueSyncBox, name: str) -> None:
    # Source is the user given name, so needs to be mapped back to a valid API value."""
    group = next(filter(lambda g: g.name == name, api.hue.groups), None)
    if group:
        await api.execution.set_state(hue_target=get_hue_target_from_id(group.id))


def current_intensity(api: aiohuesyncbox.HueSyncBox) -> str:
    sync_mode = get_sync_mode(api)
    return getattr(api.execution, sync_mode).intensity


async def select_intensity(api: aiohuesyncbox.HueSyncBox, intensity: str) -> None:
    """Set intensity for sync mode."""
    sync_mode = get_sync_mode(api)

    # Intensity is per mode so update accordingly
    state = {sync_mode: {"intensity": intensity}}
    await api.execution.set_state(**state)  # type: ignore  # noqa: PGH003


def current_sync_mode(api: aiohuesyncbox.HueSyncBox) -> str:
    return get_sync_mode(api)


async def select_sync_mode(api: aiohuesyncbox.HueSyncBox, sync_mode: str) -> None:
    """Set sync mode."""
    await api.execution.set_state(mode=sync_mode)


def current_led_indicator_mode(api: aiohuesyncbox.HueSyncBox) -> str:
    return LED_INDICATOR_MODES[api.device.led_mode]


async def select_led_indicator_mode(api: aiohuesyncbox.HueSyncBox, mode: str) -> None:
    """Set led indicator mode."""
    await api.device.set_led_mode(LED_INDICATOR_MODES.index(mode))


ENTITY_DESCRIPTIONS = [
    HueSyncBoxSelectEntityDescription(
        key="hdmi_input",
        options_fn=available_inputs,
        current_option_fn=current_input,
        select_option_fn=select_input,
    ),
    HueSyncBoxSelectEntityDescription(
        key="entertainment_area",
        options_fn=available_entertainment_areas,
        current_option_fn=current_entertainment_area,
        select_option_fn=select_entertainment_area,
    ),
    HueSyncBoxSelectEntityDescription(
        key="intensity",
        options=INTENSITIES,
        current_option_fn=current_intensity,
        select_option_fn=select_intensity,
    ),
    HueSyncBoxSelectEntityDescription(
        key="sync_mode",
        options=SYNC_MODES,
        current_option_fn=current_sync_mode,
        select_option_fn=select_sync_mode,
    ),
    HueSyncBoxSelectEntityDescription(
        key="led_indicator_mode",
        entity_category=EntityCategory.CONFIG,
        options=sorted(LED_INDICATOR_MODES),
        current_option_fn=current_led_indicator_mode,
        select_option_fn=select_led_indicator_mode,
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = config_entry.runtime_data.coordinator

    entities: list[SelectEntity] = [
        HueSyncBoxSelect(coordinator, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    ]

    async_add_entities(entities)


class HueSyncBoxSelect(CoordinatorEntity[HueSyncBoxCoordinator], SelectEntity):
    entity_description: HueSyncBoxSelectEntityDescription

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HueSyncBoxCoordinator,
        entity_description: HueSyncBoxSelectEntityDescription,
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

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
