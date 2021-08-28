# Philips Hue Play HDMI Sync Box

Custom integration for the Philips Hue Play HDMI Sync Box.

## Installation

Make sure the Philips Hue Play HDMI Sync Box has been setup with the official Hue Sync app before adding it to Home Assistant.

### HACS (https://hacs.xyz)

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant.
* Devices will be found automatically.

### Manually (when not using HACS)

* Install the custom component
  * Downloading the zip from the releases section
  * Unzip it
  * Copy it to the custom_components directory of your HA install as usual.
* Restart Home Assistant.
* Devices will be found automatically.

## Known issues

There have been reports where Home Assistant was not able to find the Philips Hue Play HDMI Sync Box.
It is unclear why it happens for some people. So far I have not been able to reproduce it which makes solving it hard.

Some workarounds that have been reported to work.

* Powercycling the Philips Hue Play HDMI Sync Box and/or restart Home Assistant and give it some time (say half an hour).
* Add `huesyncbox:` to the `configuration.yaml` file as was needed for HA versions <= 0.114.0. This should not work, but it is what users report...


## TODO

Things that can be done to improve the integration.
(not priority order)

* ~~Make repository HACS compatible~~
* ~~Add component to HACS default list (currently does not meet requirements)~~
* ~~Implement custom service to set all sync parameters at once? Could be usefull for automations~~
* ~~Add support for device actions~~
* ~~Add support for device conditions~~
* Add support for reproduce state (HA scene support)
* Extend translation for everything relevant (e.g. intensities and modes) << Doesn't seem possible right now in HA
* Find someone to make a custom card that supports the sync specific stuff
  * Remove mapping to standard media_player attributes
* ~~Write some tests~~
* Code cleanup
