# Philips Hue Play HDMI Sync Box

[![Downloads](https://img.shields.io/github/downloads/mvdwetering/huesyncbox/total.svg)](https://img.shields.io/github/downloads/mvdwetering/huesyncbox/total.svg)
[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

Custom integration for the Philips Hue Play HDMI Sync Box.

- [About](#about)
- [Device automations](#device-automations)
- [Services](#services)
- [Known issues](#known-issues)
- [Installation](#installation)
  - [HACS (recommended)](#hacs)
  - [Manually](#manually)
- [Debugging](#debugging)

## About

This integration exposes the Philips Hue Play HDMI Sync Box as a `media_player` in Home Assistant.
Functionality for controlling the syncbox has been mapped on existing `media_player` features for easy access (no need for custom cards).
For more info on how to control syncbox specific functionality not exposed through the standard `media_player` see the [Services](#services) section in this document.

The mapping is:

| Mediaplayer feature | Syncbox feature |
|---|---|
| On / Off  | On / Off  |
| Play  | Start syncing  |
| Pause  | Stop syncing  |
| Previous / Next track | Cycle syncmodes Game, Music, Video |
| Volume | Brightness |
| Source | Source |
| Sound mode  | Intensity  |

Next to this some attributes have different meaning than standard `media_player` or are explicitly added for this integration.
Note that the table below _only_ mentions differences with standard `media_player`.

| Mediaplayer attribute | Description |
|---|---|
| media_title | Shows syncmode and intensity |
| media_artist | Shows selected source |
| entertainment_area | Name of currently selected entertainment areas |
| entertainment_area_list | List with names of available entertainment areas |
| hdmi#_status | Shows status of hdmi ports. Can be unplugged, plugged, linked |
| brightness | brightness setting for the box |
| intensity | intensity setting for the box, can be subtle, moderate, high, intense |

## Device automations

A lot of features are exposed in Device automation triggers, conditions and actions.
Some examples below.

* Triggers
  * HDMI status change
  * Syncing starting/stopping (a.k.a. playing/paused)
* Conditions
  * HDMI has link
  * Is syncing (a.k.a. playing)
* Actions
  * Change brightness
  * Set intensity
  * Start sync in a specific mode
  * Select input

For complete and up-to-date list create an automation and explore the options.

## Services

The integration also exposes some services to control the box.

| Service name | Description |
|---|---|
| set_brightness | Set brightness |
| set_syncmode | Set syncmode |
| set_intensity | Set intensity |
| set_entertainment_area | Set entertainment area |
| set_sync_state | Control all aspects of the syncbox state. Allows setting multiple paramters at once, e.g. intensity and syncmode |
| set_bridge | Set the bridge to be used by the Philips Hue Play HDMI Syncbox. Keep in mind that changing the bridge by the box takes a while (about 15 seconds it seems). After the bridge has changed you might need to select the `entertainment_area` if connectionstate is `invalidgroup` instead of `connected`. |

For the most up-to-date list and parameter descriptions use the Services tab in the Developer tools and search for `huesyncbox` in the services list.

## Known issues

There have been reports where Home Assistant was not able to find the Philips Hue Play HDMI Sync Box automatically.
It is unclear why it happens for some people. So far I have not been able to reproduce it which makes solving it hard.

However it is now possible to add the syncbox manually through the "Add Integration" button where you can input the IP and ID of the box.

In case manual addition also does not work here are some workarounds that have been reported to work.

* Powercycling the Philips Hue Play HDMI Sync Box and/or restart Home Assistant and give it some time (say half an hour).
* Add `huesyncbox:` to the `configuration.yaml` file as was needed for HA versions <= 0.114.0. This should not work, but it is what users report...


## Installation

> **Warning** 
> Make sure the Philips Hue Play HDMI Sync Box has been setup with the official Hue Sync app before adding it to Home Assistant.

### HACS

**Recommended because you will get notified of updates**

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen

### Manually

**when not using HACS**

* Install the custom component
  * Download the zip from the releases section on Github
  * Unzip it
  * Copy it to the custom_components directory of your Home Assistnat install as usual
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen

## Debugging
To enable debug logging for this integration, you can control this in your Home Assistant `configuration.yaml` file.

For example : 
```yaml
logger: 
  default: info
  logs:
    custom_components.huesyncbox: debug
    aiohuesyncbox: debug
```