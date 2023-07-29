"""Constants for the Philips Hue Play HDMI Sync Box integration."""
import logging

DOMAIN = "huesyncbox"
LOGGER = logging.getLogger(__package__)

DEFAULT_PORT = 443


MANUFACTURER_NAME = "Signify"


INTENSITY_SUBTLE = "subtle"
INTENSITY_MODERATE = "moderate"
INTENSITY_HIGH = "high"
INTENSITY_INTENSE = "intense"

MODE_VIDEO = "video"
MODE_MUSIC = "music"
MODE_GAME = "game"

MODES = [MODE_VIDEO, MODE_MUSIC, MODE_GAME]