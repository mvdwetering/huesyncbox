import asyncio
from datetime import timedelta
import textwrap

import aiohuesyncbox
import async_timeout
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_BRIGHTNESS_STEP
from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOUND_MODE,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_SET,
)
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PLAYING

from .const import (
    ATTR_ENTERTAINMENT_AREA,
    ATTR_INPUT,
    ATTR_INPUT_NEXT,
    ATTR_INPUT_PREV,
    ATTR_INTENSITY,
    ATTR_INTENSITY_NEXT,
    ATTR_INTENSITY_PREV,
    ATTR_MODE,
    ATTR_MODE_NEXT,
    ATTR_MODE_PREV,
    ATTR_SYNC,
    ATTR_SYNC_TOGGLE,
    DOMAIN,
    INTENSITIES,
    LOGGER,
    MODES,
)

from .helpers import log_config_entry, redacted
from .huesyncbox import (
    PhilipsHuePlayHdmiSyncBox,
    async_retry_if_someone_else_is_syncing,
)

SUPPORT_HUESYNCBOX = (
    SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE
    | SUPPORT_PLAY
    | SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_VOLUME_SET
    | SUPPORT_SELECT_SOUND_MODE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
)

SCAN_INTERVAL = timedelta(seconds=2)

MAX_BRIGHTNESS = 200


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup from configuration.yaml, not supported, only through integration."""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup from config_entry."""
    LOGGER.debug(
        "%s async_setup_entry\nconfig_entry:\n%s\nhass.data\n%s"
        % (
            __name__,
            textwrap.indent(log_config_entry(config_entry), "  "),
            [redacted(v) for v in hass.data[DOMAIN].keys()],
        )
    )
    entity = HueSyncBoxMediaPlayerEntity(
        hass.data[DOMAIN][config_entry.data["unique_id"]]
    )
    async_add_entities([entity], update_before_add=True)


async def async_unload_entry(hass, config_entry):
    # Not sure what to do, entities seem to disappear by themselves
    # No other de-initialization seems needed
    pass


class HueSyncBoxMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a HueSyncBox as mediaplayer."""

    def __init__(self, huesyncbox: PhilipsHuePlayHdmiSyncBox) -> None:
        self._huesyncbox = huesyncbox
        self._available = False
        huesyncbox.entity = self

    @property
    def device_info(self):
        """Return the device info."""
        # Only return the identifiers so the entry gets linked properly
        # Managing deviceinfo is done elsewhere
        return {
            "identifiers": {(DOMAIN, self._huesyncbox.api.device.unique_id)},
        }

    async def async_update(self):
        try:
            with async_timeout.timeout(5):
                # Since we need to update multiple endpoints just update all in one call
                old_device = self._huesyncbox.api.device
                await self._huesyncbox.api.update()
                if old_device != self._huesyncbox.api.device:
                    await self._huesyncbox.async_update_registered_device_info()
                self._available = True
        except (asyncio.TimeoutError, aiohuesyncbox.AiohuesyncboxException):
            self._available = False

    @property
    def unique_id(self):
        """Return the uniqueid of the entity."""
        return self._huesyncbox.api.device.unique_id

    @property
    def available(self):
        """Return if the device is available or not."""
        return self._available

    @property
    def name(self):
        """Return the name of the entity."""
        return self._huesyncbox.api.device.name

    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        supported_commands = SUPPORT_HUESYNCBOX
        return supported_commands

    @property
    def state(self):
        """Return the state of the entity."""
        state = STATE_PLAYING
        device_state = self._huesyncbox.api.execution.mode
        if device_state == "powersave":
            state = STATE_OFF
        if device_state == "passthrough":
            state = STATE_IDLE
        return state

    async def async_turn_off(self):
        """Turn off media player."""
        await self._huesyncbox.api.execution.set_state(mode="powersave")

    async def async_turn_on(self):
        """Turn the media player on."""
        await self._huesyncbox.api.execution.set_state(mode="passthrough")

    async def async_media_play(self):
        """Send play command."""
        await async_retry_if_someone_else_is_syncing(
            self._huesyncbox,
            lambda: self._huesyncbox.api.execution.set_state(sync_active=True),
        )

    async def async_media_pause(self):
        """Send pause command."""
        # Syncbox does not really have "pause", but the default mediaplayer
        # card does not work when the mediaplayer only supports Stop,
        # so lets implement pause for now to work around that
        await self.async_media_stop()

    async def async_media_stop(self):
        """Send stop command."""
        await self._huesyncbox.api.execution.set_state(sync_active=False)

    @property
    def source(self):
        """Return the current input source."""
        selected_source = self._huesyncbox.api.execution.hdmi_source
        for input in self._huesyncbox.api.hdmi.inputs:
            if input.id == selected_source:
                return input.name

    @property
    def source_list(self):
        """List of available input sources."""
        sources = []
        for input in self._huesyncbox.api.hdmi.inputs:
            sources.append(input.name)
        return sorted(sources)

    async def async_select_source(self, source):
        """Select input source."""
        # Source is the user given name, so needs to be mapped back to a valid API value."""
        for input in self._huesyncbox.api.hdmi.inputs:
            if input.name == source:
                await self._huesyncbox.api.execution.set_state(hdmi_source=input.id)
                break

    @staticmethod
    def get_hue_target_from_id(id: str):
        try:
            return f"groups/{int(id)}"
        except ValueError:
            return id

    async def async_select_entertainment_area(self, area_name):
        """Select entertainmentarea."""
        # Area is the user given name, so needs to be mapped back to a valid API value."""
        group = self._get_group_from_area_name(area_name)
        if group:
            await self._huesyncbox.api.execution.set_state(
                hue_target=self.get_hue_target_from_id(group.id)
            )

    def _get_group_from_area_name(self, area_name):
        """Get the group object by entertainment area name."""
        for group in self._huesyncbox.api.hue.groups:
            if group.name == area_name:
                return group
        return None

    def _get_entertainment_areas(self):
        """List of available entertainment areas."""
        areas = []
        for group in self._huesyncbox.api.hue.groups:
            areas.append(group.name)
        return sorted(areas)

    def _get_selected_entertainment_area(self):
        """Return the name of the active entertainment area."""
        hue_target = (
            self._huesyncbox.api.execution.hue_target
        )  # note that this is a string like "groups/123"
        selected_area = None
        try:
            id = hue_target.replace("groups/", "")
            for group in self._huesyncbox.api.hue.groups:
                if group.id == id:
                    selected_area = group.name
                    break
        except KeyError:
            LOGGER.warning("Selected entertainment area not available in groups")
        return selected_area

    @property
    def device_state_attributes(self):
        api = self._huesyncbox.api
        mode = api.execution.mode

        attributes = {
            "mode": mode,
            "entertainment_area_list": self._get_entertainment_areas(),
            "entertainment_area": self._get_selected_entertainment_area(),
        }

        for index in range(len(api.hdmi.inputs)):
            attributes[f"hdmi{index+1}_status"] = api.hdmi.inputs[index].status

        if mode != "powersave":
            attributes["brightness"] = self.scale(
                api.execution.brightness, [0, MAX_BRIGHTNESS], [0, 1]
            )
            if not mode in MODES:
                mode = api.execution.last_sync_mode
            attributes["intensity"] = getattr(api.execution, mode).intensity
        return attributes

    async def async_set_sync_state(self, sync_state):
        """Set sync state."""

        # Special handling for Toggle specific mode as that cannot be done in 1 call on the API
        sync_toggle = sync_state.get(ATTR_SYNC_TOGGLE, None)
        mode = sync_state.get(ATTR_MODE, None)
        if sync_toggle and mode:
            if self._huesyncbox.api.execution.mode != mode:
                # When not syncing in the desired mode, just turn on the desired mode, no toggle
                sync_toggle = None
            else:
                # Otherwise just toggle, no mode (setting mode would interfere with the toggle)
                mode = None

        # Entertainment area
        group = self._get_group_from_area_name(
            sync_state.get(ATTR_ENTERTAINMENT_AREA, None)
        )
        hue_target = self.get_hue_target_from_id(group.id) if group else None

        state = {
            "sync_active": sync_state.get(ATTR_SYNC, None),
            "sync_toggle": sync_toggle,
            # "hdmi_active": ,
            # "hdmi_active_toggle": None,
            "mode": mode,
            "mode_cycle": "next"
            if ATTR_MODE_NEXT in sync_state
            else "previous"
            if ATTR_MODE_PREV in sync_state
            else None,
            "hdmi_source": sync_state.get(ATTR_INPUT, None),
            "hdmi_source_cycle": "next"
            if ATTR_INPUT_NEXT in sync_state
            else "previous"
            if ATTR_INPUT_PREV in sync_state
            else None,
            "brightness": int(
                self.scale(sync_state[ATTR_BRIGHTNESS], [0, 1], [0, MAX_BRIGHTNESS])
            )
            if ATTR_BRIGHTNESS in sync_state
            else None,
            "brightness_step": int(
                self.scale(
                    sync_state[ATTR_BRIGHTNESS_STEP],
                    [-1, 1],
                    [-MAX_BRIGHTNESS, MAX_BRIGHTNESS],
                )
            )
            if ATTR_BRIGHTNESS_STEP in sync_state
            else None,
            "intensity": sync_state.get(ATTR_INTENSITY, None),
            "intensity_cycle": "next"
            if ATTR_INTENSITY_NEXT in sync_state
            else "previous"
            if ATTR_INTENSITY_PREV in sync_state
            else None,
            "hue_target": hue_target,
        }

        try:
            await async_retry_if_someone_else_is_syncing(
                self._huesyncbox,
                lambda: self._huesyncbox.api.execution.set_state(**state),
            )
        except aiohuesyncbox.RequestError as e:
            if "13: Invalid Key" in e.args[0]:
                # Clarify this specific case as people will run into it
                # Use a warning so it is visually separated from the actual error
                LOGGER.warning(
                    "This error most likely occured because the service call resulted in an empty message to the syncbox. Make sure that the selected options would result in an action on the syncbox (e.g. requesting only `sync_toggle:false` would cause such an error)."
                )
            raise

    async def async_set_sync_mode(self, sync_mode):
        """Select sync mode."""
        await async_retry_if_someone_else_is_syncing(
            self._huesyncbox,
            lambda: self._huesyncbox.api.execution.set_state(mode=sync_mode),
        )

    async def async_set_intensity(self, intensity, mode):
        """Set intensity for sync mode."""
        if mode == None:
            mode = self.get_mode()

        # Intensity is per mode so update accordingly
        state = {mode: {"intensity": intensity}}
        await self._huesyncbox.api.execution.set_state(**state)

    async def async_set_brightness(self, brightness):
        """Set brightness"""
        api_brightness = self.scale(brightness, [0, 1], [0, MAX_BRIGHTNESS])
        await self._huesyncbox.api.execution.set_state(brightness=api_brightness)

    def get_mode(self):
        mode = self._huesyncbox.api.execution.mode
        if not self._huesyncbox.api.execution.mode in MODES:
            mode = self._huesyncbox.api.execution.last_sync_mode
        return mode

    @staticmethod
    def scale(input_value, input_range, output_range):
        input_min = input_range[0]
        input_max = input_range[1]
        input_spread = input_max - input_min

        output_min = output_range[0]
        output_max = output_range[1]
        output_spread = output_max - output_min

        value_scaled = float(input_value - input_min) / float(input_spread)

        return output_min + (value_scaled * output_spread)

    # Below properties and methods are temporary to get a "free" UI with the mediaplayer card

    @property
    def volume_level(self):
        """Volume level of the media player (0..1) is mapped brightness for free UI."""
        return self.scale(
            self._huesyncbox.api.execution.brightness, [0, MAX_BRIGHTNESS], [0, 1]
        )

    async def async_set_volume_level(self, volume):
        """Set volume level of the media player (0..1), abuse to control brightness for free UI."""
        await self.async_set_brightness(volume)

    @property
    def sound_mode(self):
        """Return the current sound mode (actually intensity)."""
        attributes = self.device_state_attributes
        if "intensity" in attributes:
            return attributes["intensity"]
        return None

    @property
    def sound_mode_list(self):
        """List of available soundmodes / intensities."""
        return INTENSITIES

    async def async_select_sound_mode(self, sound_mode):
        """Select sound mode, abuse for intensity to get free UI."""
        await self.async_set_intensity(sound_mode, None)

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        # Pretend we are playing music to expose additional data (e.g. mode and intensity) to the player
        return MEDIA_TYPE_MUSIC

    @property
    def media_title(self):
        """Title of current playing media, abuse to disaplay mode + intensity for free UI."""
        return f"{self.get_mode().capitalize()} - {self.sound_mode.capitalize()}"

    @property
    def media_artist(self):
        """Title of current playing media, abuse to display current source so I have a free UI."""
        return self.source

    async def async_media_previous_track(self):
        """Send previous track command, abuse to cycle modes for now."""
        await self._huesyncbox.api.execution.cycle_sync_mode(False)

    async def async_media_next_track(self):
        """Send next track command, abuse to cycle modes for now."""
        await self._huesyncbox.api.execution.cycle_sync_mode(True)
