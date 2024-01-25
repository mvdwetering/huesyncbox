# Philips Hue Play HDMI Sync Box

[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

Custom integration for the Philips Hue Play HDMI Sync Box.

- [About](#about)
  - [Behavior](#behavior)
  - [Services](#services)
- [Updating from before version 2](#updating-from-before-version-20)
- [Installation](#installation)
  - [Home Assistant Community Store (recommended)](#home-assistant-community-store-hacs)
  - [Manually](#manually)

## About

> Please setup the Philips Hue Play HDMI Syncbox with the Hue App first and make sure it works before setting up this integration.

This integration exposes the Philips Hue Play HDMI Sync Box in Home Assistant so it can be used in automations or dashboards.

The Philips Hue Play HDMI Sync Box will be discovered automatically in most cases and can be added manually through the `Settings > Devices and Services` menu in Home Assistant if that is not the case.

The following features are available:

* Power on/off
* Light sync on/off
* Intensity (subtle/moderate/high/intense)
* Sync mode (video/music/game)
* HDMI Input selection
* Brightness control
* Entertainment area selection
* HDMI1-4 connection status
* Dolby Vision compatibility on/off
* LED indicator mode
* Bridge connection status ⁺
* Bridge ID ⁺
* IP address ⁺
* Wifi quality ⁺

Entities marked with ⁺ are default disabled.

### Behavior

A few notes on behavior when changing entities.

* Enabling light sync will also power on the box
* Setting sync mode will also power on the box and start light sync on the selected mode
* When you want to change multiple entities the order is important. For example Intensity applies to the current selected mode. So if you want to change both the `intensity` and `mode` you _first_ have to change the mode and then set the intensity. Otherwise the intensity is applied to the "old" mode. If you want to avoid ordering issues you can use the `set_sync_state` service which will take care of the ordering and is more efficient.

### Services

The integration exposes some additional services.

For the parameter descriptions use the Services tab in the Home Assistant Developer tools and search for `huesyncbox` in the services list.

| Service name | Description |
|---|---|
| set_bridge | Set the bridge to be used by the Philips Hue Play HDMI Syncbox. |
| set_sync_state | Set the state of multiple features of the Philips Hue Play HDMI Syncbox at once. Makes sure everything is set in the correct order and is more efficient compared to using separate commands. |

## Updating from before version 2.0

The 2.0 version is a complete rewrite to allow for multiple entities and modernize the integration in general, however it is a big breaking change.

See the [release notes for 2.0.0](https://github.com/mvdwetering/huesyncbox/releases/tag/v2.0.0) for more details on the changes and migration.

No functionality is lost it just moved to a different place.

## Installation

> **Note**
> The Wifi connection of the Philips Hue Play HDMI Sync Box has to be setup with the official Hue app before it can be added to Home Assistant.

### Home Assistant Community Store (HACS)

HACS is a 3rd party downloader for Home Assistant to easily install and update custom integrations made by the community. More information and installation instructions can be found on their site https://hacs.xyz/

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen

### Manually

* Install the custom component
  * Download the zip from the releases section on Github
  * Unzip it
  * Copy it to the custom_components directory of your Home Assistnat install as usual
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen
