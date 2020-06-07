"""Constants for the Philips Hue Play HDMI Sync Box integration."""

import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "huesyncbox"

MANUFACTURER_NAME = "Signify"

HUESYNCBOX_ATTR_BRIGHTNESS = "brightness"
HUESYNCBOX_ATTR_MODE = "mode"
HUESYNCBOX_ATTR_INTENSITY = "intensity"

HUESYNCBOX_INTENSITIES = ['subtle', 'moderate', 'high', 'intense']
HUESYNCBOX_MODES = ['video', 'music', 'game']
