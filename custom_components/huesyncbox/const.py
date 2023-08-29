"""Constants for the Philips Hue Play HDMI Sync Box integration."""
from datetime import timedelta
import logging

DOMAIN = "huesyncbox"
LOGGER = logging.getLogger(__package__)

DEFAULT_PORT = 443

COORDINATOR_UPDATE_INTERVAL = timedelta(seconds=3)


MANUFACTURER_NAME = "Signify"

REGISTRATION_ID = "registration_id"

INTENSITY_SUBTLE = "subtle"
INTENSITY_MODERATE = "moderate"
INTENSITY_HIGH = "high"
INTENSITY_INTENSE = "intense"
INTENSITIES = [INTENSITY_SUBTLE, INTENSITY_MODERATE, INTENSITY_HIGH, INTENSITY_INTENSE]

SYNC_MODE_VIDEO = "video"
SYNC_MODE_MUSIC = "music"
SYNC_MODE_GAME = "game"
SYNC_MODES = [SYNC_MODE_VIDEO, SYNC_MODE_MUSIC, SYNC_MODE_GAME]

INPUT_HDMI1 = "input1"
INPUT_HDMI2 = "input2"
INPUT_HDMI3 = "input3"
INPUT_HDMI4 = "input4"
INPUTS = [INPUT_HDMI1, INPUT_HDMI2, INPUT_HDMI3, INPUT_HDMI4]

SERVICE_SET_BRIDGE = "set_bridge"
ATTR_BRIDGE_ID = "bridge_id"
ATTR_BRIDGE_USERNAME = "bridge_username"
ATTR_BRIDGE_CLIENTKEY = "bridge_clientkey"

SERVICE_SET_SYNC_STATE = "set_sync_state"
ATTR_POWER = "power"
ATTR_SYNC = "sync"
ATTR_MODE = "mode"
ATTR_INTENSITY = "intensity"
ATTR_INPUT = "input"
ATTR_ENTERTAINMENT_AREA = "entertainment_area"
