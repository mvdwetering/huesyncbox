# Philips Hue Play HDMI Sync Box

[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

Custom integration for the Philips Hue Play HDMI Sync Box.

- [About](#about)
  - [Behavior](#behavior)
  - [Services](#services)
 - [Known issues](#known-issues)
- [Updating from before version 2](#updating-from-before-version-20)
- [Installation](#installation)
  - [HACS (recommended)](#hacs)
  - [Manually](#manually)

## About

This integration exposes the Philips Hue Play HDMI Sync Box in Home Assistant so it can be used in automations or dashboards.

The following features are available:

* Power on/off
* Light sync on/off
* Intensity (subtle/moderate/high/intense)
* Sync mode (video/music/game)
* HDMI Input selection
* Brightness control
* HDMI1-4 connection status
* Dolby Vision compatibility on/off
* LED indicator mode
* Bridge connection status (default disabled)
* Bridge ID (default disabled)
* IP address (default disabled)
* Wifi quality (default disabled)

### Behavior

A few notes on behaviour when changing entities.

* Enabling light sync will also power on the box
* Setting sync mode will also power on the box and start light sync on the selected mode
* When you want to change multiple entities the order is important. For example Intensity applies to the current selected mode. So if you want to change both the `intensity` and `mode` you _first_ have to change the mode and then set the intensity. Otherwise the intensity is applied to the "old" mode. If you want to avoid ordering issues you can use the `set_sync_state` service which will take care of the ordering and is more efficient.


### Services

The integration exposes some additional services.

| Service name | Description |
|---|---|
| set_bridge | Set the bridge to be used by the Philips Hue Play HDMI Syncbox. Keep in mind that changing the bridge by the box takes a while (about 15 seconds it seems). After the bridge has changed you might need to select an entertainment area if Bridge connection state is `invalidgroup` instead of `connected`. |
| set_sync_state | Set the state of multiple features of the Philips Hue Play HDMI Syncbox at once. Makes sure everything is set in the correct order and is more efficient compared to using separate commands. |

For the most up-to-date list and parameter descriptions use the Services tab in the Developer tools and search for `huesyncbox` in the services list.


## Known issues

There have been reports where Home Assistant was not able to find the Philips Hue Play HDMI Sync Box automatically.
It is unclear why it happens for some people. So far I have not been able to reproduce it which makes solving it hard.

Powercycling the Philips Hue Play HDMI Sync Box and/or restart Home Assistant sometimes helps.

If still not found automatically it is possible to add the syncbox manually through the "Add Integration" button and follow the instructions.


## Updating from before version 2.0

Before 2.0 the functionality of the Philips Hue Play HDMI Sync Box was all exposed through one single mediaplayer entity. Several features of the media_player were abused to control things on the box. E.g. brightness was controlled by the volume slider. This turned out to be confusing and quite limiting. Next to that the way the integration was built did not allow for more entities so it was not possible to extend it. 

The 2.0 version is a complete rewrite to allow for multiple entities and modernize the integration in general. Having multiple standard entities should make it clear what entity does what.

No functionality is lost it just moved to a different place.

See the [release notes for 2.0.0](https://github.com/mvdwetering/huesyncbox/releases/tag/v2.0.0b0) for more details on the changes and migration.


## Installation

> **Note**
> The Philips Hue Play HDMI Sync Box has to be setup with the official Hue app before adding it to Home Assistant.

### HACS

> **Note**
> Recommended because you will get notified of updates

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen

### Manually

> **Note**
> When not using HACS

* Install the custom component
  * Download the zip from the releases section on Github
  * Unzip it
  * Copy it to the custom_components directory of your Home Assistnat install as usual
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen
