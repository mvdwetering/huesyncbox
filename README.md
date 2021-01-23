# Philips Hue Play HDMI Sync Box

Custom integration for the Philips Hue Play HDMI Sync Box.

> Since HA 0.114 it is not needed to have `huesyncbox:` in your `configuration.yaml` anymore. Please remove it to avoid possible issues in the future.

## Installation

Make sure the Philips Hue Play HDMI Sync Box has been setup with the official Hue Sync app before adding it to Home Assistant.

### HACS (https://hacs.xyz)

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant.
* Devices will be found automatically.

### Manually (when not using HACS)

* Install the custom component by downloading it and copy it to the custom_components directory as usual.
* Restart Home Assistant.
* Devices will be found automatically.

## TODO

Things that can be done to improve the integration.
(not priority order)

* ~~Make repository HACS compatible~~
* ~~Add component to HACS default list (currently does not meet requirements)~~
* ~~Implement custom service to set all sync parameters at once? Could be usefull for automations~~
* ~~Add support for device actions~~
* Add support for device conditions
* Add support for reproduce state (HA scene support)
* Extend translation for everything relevant (e.g. intensities and modes)
* Find someone to make a custom card that supports the sync specific stuff
  * Remove mapping to standard media_player attributes
* Write some tests
* Code cleanup
