# Philips Hue Play HDMI Sync Box

[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

Custom integration for the Philips Hue Play HDMI Sync Box.

- [About](#about)
  - [Behaviour](#behaviour)
  - [Services](#services)
 - [Known issues](#known-issues)
- [Updating from before version 2](#updating-from-before-version-20)
- [Installation](#installation)
  - [HACS (recommended)](#hacs)
  - [Manually](#manually)

## About

This integration exposes functionality of the Philips Hue Play HDMI Sync Box as entities in Home Assistant so it can be used in automation or from the dashboard.

Exposed entities:

* Power on/off
* Light sync on/off
* Intensity subtle/moderate/high/intense
* Mode video/music/game
* Brightness
* Dolby Vision compatibility on/off
* HDMI1-4 connection status
* Bridge connection status (default disabled)
* Bridge ID (default disabled)
* IP address (default disabled)

### Behaviour

A few notes on behaviour when changing entities.

* Intensity applies to the current selected mode. So if you want to change both the intensity and mode you _first_ have to change the mode and then set the intensity. Otherwise the intensity is applied to the "old" mode
* When enabling light sync, the box will power on automatically
* Changing mode will power on the box and start light sync on that mode

This behaviour is what happens when sending commands to the box and is a bit different on how the Hue app controls the syncbox as it seems to only send the settings when starting syncing (or while already syncing). Emulating this behaviour in Home Assistant is complicated and in general not recommended (or even allowed).


### Services

The integration exposes some services to control functionality that can not be exposed on entities.

| Service name | Description |
|---|---|
| set_bridge | Set the bridge to be used by the Philips Hue Play HDMI Syncbox. Keep in mind that changing the bridge by the box takes a while (about 15 seconds it seems). After the bridge has changed you might need to select an entertainment area if Bridge connection state is `invalidgroup` instead of `connected`. |

For the most up-to-date list and parameter descriptions use the Services tab in the Developer tools and search for `huesyncbox` in the services list.


## Known issues

There have been reports where Home Assistant was not able to find the Philips Hue Play HDMI Sync Box automatically.
It is unclear why it happens for some people. So far I have not been able to reproduce it which makes solving it hard.

Powercycling the Philips Hue Play HDMI Sync Box and/or restart Home Assistant sometimes helps.

If still not found automatically it is possible to add the syncbox manually through the "Add Integration" button and follow the instructions.


## Updating from before version 2.0

Before 2.0 the functionality of the Philips Hue Play HDMI Sync Box was all exposed through one single mediaplayer entity. Several features of the media_player were abused to control things on the box. E.g. brightness was controlled by the volume slider. This turned out to be confusing and quite limiting. Next to that the way the integration was built did not allow for more entities so it was not possible to extend it. 

The 2.0 version is a complete rewrite to allow for multiple entities and modernize the integration in general. Having multiple standard entities should make it clear what entity does what.

> **Warning**
> This change means that existing automations will need to be updated to use the new entities!
> Home Assistant will create repairs when using the obsolete items which should help in finding the relevant places that need to be updated.

With the transition to the new entities most custom services that were offered became obsolete as native Home Assistant services of the entities can be used now. 
Information exposed by additional attributes on the `media_player` is available on the new entities.

No functionality is lost it just moved to a different place.

Below is a list of old services and the replacement to help with the transition.

| Old service name | Replaced by |
|---|---|
| set_brightness | Use services of the brightness entity |
| set_syncmode | Use services of the sync mode entity |
| set_intensity | Use services of the intensity entity |
| set_entertainment_area | Use services of the entertainment area entity |
| set_sync_state | Obsolete, use services on the specific entities instead |
| set_bridge | Unchanged |


## Installation

> **Note**
> The Philips Hue Play HDMI Sync Box has to be setup with the official Hue app before adding it to Home Assistant.

### HACS

> **Note** Recommended because you will get notified of updates

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

