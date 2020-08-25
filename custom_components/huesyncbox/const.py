"""Constants for the Philips Hue Play HDMI Sync Box integration."""

import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "huesyncbox"

MANUFACTURER_NAME = "Signify"

SERVICE_SET_SYNC_STATE = 'set_sync_state'
SERVICE_SET_BRIGHTNESS = 'set_brightness'
SERVICE_SET_INTENSITY = 'set_intensity'
SERVICE_SET_MODE = 'set_sync_mode'

ATTR_SYNC = 'sync'
ATTR_SYNC_TOGGLE = 'sync_toggle'

ATTR_MODE = 'mode'
ATTR_MODE_NEXT = 'mode_next'
ATTR_MODE_PREV = 'mode_prev'

MODE_VIDEO = 'video'
MODE_MUSIC = 'music'
MODE_GAME = 'game'

MODES = [ MODE_VIDEO, MODE_MUSIC, MODE_GAME ]

ATTR_INTENSITY = "intensity"
ATTR_INTENSITY_NEXT = "intensity_next"
ATTR_INTENSITY_PREV = "intensity_prev"

INTENSITY_SUBTLE = "subtle"
INTENSITY_MODERATE = "moderate"
INTENSITY_HIGH = "high"
INTENSITY_INTENSE = "intense"

INTENSITIES = [ INTENSITY_SUBTLE, INTENSITY_MODERATE, INTENSITY_HIGH, INTENSITY_INTENSE ]

ATTR_INPUT = "input"
ATTR_INPUT_NEXT = "input_next"
ATTR_INPUT_PREV = "input_prev"

INPUT_HDMI1 = 'input1'
INPUT_HDMI2 = 'input2'
INPUT_HDMI3 = 'input3'
INPUT_HDMI4 = 'input4'

INPUTS = [ INPUT_HDMI1, INPUT_HDMI2, INPUT_HDMI3, INPUT_HDMI4 ]
