# Philips Hue Play HDMI Sync Box

Custom component for Philips Hue Play HDMI Sync Box devices.

## Installation

* Make sure the Philips Hue Play HDMI Sync Box has been setup with the official Hue Sync app.
* Add `huesyncbox:` to `configuration.yaml` and restart Home Assistant. Devices will be found automatically.

## Known issues

* Linking fails the first time, but works second time (I know what it is just need to get it fixed somehow)

## TODO

Things still to do before it is "done"
(not priority order)

* Fix known issues
* Make repository HACS compatible
* Implement custom service to set all sync parameters at once? Could be usefull for automations
* Add support for device actions
* Add support for device conditions
* Add support for reproduce state
* Extend translation for everything relevant (e.g. intensities and modes)
* Find someone to make a custom card that supports the sync specific stuff
  * Remove mapping to standard media_player attributes
* Write some tests
* Code cleanup
* Submit to HA official repo
