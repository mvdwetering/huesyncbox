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

SYNC_MODE_VIDEO = "video"
SYNC_MODE_MUSIC = "music"
SYNC_MODE_GAME = "game"

SYNC_MODES = [SYNC_MODE_VIDEO, SYNC_MODE_MUSIC, SYNC_MODE_GAME]


SERVICE_SET_BRIDGE = "set_bridge"

ATTR_BRIDGE_ID = "bridge_id"
ATTR_BRIDGE_USERNAME = "bridge_username"
ATTR_BRIDGE_CLIENTKEY = "bridge_clientkey"
