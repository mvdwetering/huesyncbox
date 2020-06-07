import logging

import asyncio
import async_timeout

from homeassistant.components.media_player import (
    MediaPlayerEntity, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import (
    SUPPORT_TURN_OFF, SUPPORT_TURN_ON, SUPPORT_SELECT_SOURCE, SUPPORT_PLAY, SUPPORT_STOP, SUPPORT_PAUSE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_STEP, SUPPORT_SELECT_SOUND_MODE, MEDIA_TYPE_MUSIC, SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK)
from homeassistant.const import (
    STATE_OFF, STATE_IDLE, STATE_PLAYING
)

from .const import DOMAIN, LOGGER, MANUFACTURER_NAME, HUESYNCBOX_MODES, HUESYNCBOX_INTENSITIES

import aiohuesyncbox

SUPPORT_HUESYNCBOX = SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE | SUPPORT_PLAY | SUPPORT_PAUSE | SUPPORT_STOP | SUPPORT_VOLUME_SET | SUPPORT_SELECT_SOUND_MODE | SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK

MAX_BRIGHTNESS = 200

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup from configuration.yaml, not supported, only through integration."""
    pass

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup from config_entry."""
    device = HueSyncBoxMediaPlayerEntity(hass.data[DOMAIN][config_entry.data["unique_id"]])
    async_add_entities([device], update_before_add=True)

async def async_unload_entry(hass, config_entry):
    # Not sure what to do, entities seem to disappear by themselves
    # No other de-initialization seems needed
    pass


class HueSyncBoxMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a HueSyncBox as mediaplayer."""

    def __init__(self, huesyncbox):
        self._huesyncbox = huesyncbox
        self._available = False
        huesyncbox.entity = self

    @property
    def device_info(self):
        """Return the device info."""
        return {
            'identifiers': {
                (DOMAIN, self._huesyncbox.api.device.unique_id)
            },
            'name': self._huesyncbox.api.device.name,
            'manufacturer': MANUFACTURER_NAME,
            'model': self._huesyncbox.api.device.device_type,
            'sw_version': self._huesyncbox.api.device.firmware_version,
        }

    async def async_update(self):
        try:
            with async_timeout.timeout(5):
                # Since we need to update multiple endpoints just update all in one call
                await self._huesyncbox.api.update()
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
        if device_state == 'powersave':
            state = STATE_OFF
        if device_state == 'passthrough':
            state = STATE_IDLE
        return state

    async def async_turn_off(self):
        """Turn off media player."""
        await self._huesyncbox.api.execution.set_state(mode='powersave')
        self.async_schedule_update_ha_state()

    async def async_turn_on(self):
        """Turn the media player on."""
        await self._huesyncbox.api.execution.set_state(mode='passthrough')
        self.async_schedule_update_ha_state()

    async def async_media_play(self):
        """Send play command."""
        try:
            await self._huesyncbox.api.execution.set_state(sync_active=True)
        except aiohuesyncbox.InvalidState:
            # Most likely another application is already syncing to the bridge
            # Since there is no way to ask the user what to do just
            # stop the active application and try to activate again
            for id, info in self._huesyncbox.api.hue.groups.items():
                if info["active"]:
                    LOGGER.info(f'Deactivating syncing for {info["owner"]}')
                    await self._huesyncbox.api.hue.set_group_state(id, active=False)
            await self._huesyncbox.api.execution.set_state(sync_active=True)

        self.async_schedule_update_ha_state()

    async def async_media_pause(self):
        """Send pause command."""
        # Syncbox does not really have "pause", but the default mediaplayer
        # card does not work when the mediaplayer only supports Stop,
        # so lets implement pause for now to work around that
        await self.async_media_stop()

    async def async_media_stop(self):
        """Send stop command."""
        await self._huesyncbox.api.execution.set_state(sync_active=False)
        self.async_schedule_update_ha_state()

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
                self.async_schedule_update_ha_state()
                break

    @property
    def device_state_attributes(self):
        api = self._huesyncbox.api
        mode = api.execution.mode
        attributes =  {
            'mode': mode,
        }

        if mode != 'powersave':
            attributes['brightness'] = self.scale(api.execution.brightness, [0, MAX_BRIGHTNESS], [0, 1])
            if not mode in HUESYNCBOX_MODES:
                mode = api.execution.last_sync_mode
            attributes['intensity'] = getattr(api.execution, mode).intensity
        return attributes

    async def async_set_sync_mode(self, sync_mode):
        """Select sync mode."""
        await self._huesyncbox.api.execution.set_state(mode=sync_mode)
        self.async_schedule_update_ha_state()

    async def async_set_intensity(self, intensity, mode):
        """Set intensity for sync mode."""
        if mode == None:
            mode = self.get_mode()

        # Intensity is per mode so update accordingly
        state = {
            mode: {'intensity': intensity}
        }
        await self._huesyncbox.api.execution.set_state(**state)
        self.async_schedule_update_ha_state()

    async def async_set_brightness(self, brightness):
        """Set brightness"""
        api_brightness = self.scale(brightness, [0, 1], [0, MAX_BRIGHTNESS])
        await self._huesyncbox.api.execution.set_state(brightness=api_brightness)
        self.async_schedule_update_ha_state()

    @property
    def volume_level(self):
        """Volume level of the media player (0..1) is mapped brightness for free UI."""
        return self.scale(self._huesyncbox.api.execution.brightness, [0, MAX_BRIGHTNESS], [0, 1])

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
        return HUESYNCBOX_INTENSITIES

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

    def get_mode(self):
        mode = self._huesyncbox.api.execution.mode
        if not self._huesyncbox.api.execution.mode in HUESYNCBOX_MODES:
            mode = self._huesyncbox.api.execution.last_sync_mode
        return mode

    @property
    def media_artist(self):
        """Title of current playing media, abuse to display current source so I have a free UI."""
        return self.source

    async def async_media_previous_track(self):
        """Send previous track command, abuse to cycle modes for now."""
        await self._huesyncbox.api.execution.cycle_sync_mode(False)
        self.async_schedule_update_ha_state()

    async def async_media_next_track(self):
        """Send next track command, abuse to cycle modes for now."""
        await self._huesyncbox.api.execution.cycle_sync_mode(True)
        self.async_schedule_update_ha_state()

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