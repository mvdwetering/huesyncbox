# Philips Hue Play HDMI Sync Box

Custom integration for the Philips Hue Play HDMI Sync Box.

This integration exposes the Philips Hue Play HDMI Sync Box as a `media_player` in Home Assistant. 
Functionality for controlling the syncbox has been mapped on existing `media_player` features for easy access (no need for custom cards).

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

For complete list create an automation and explore the options.

## Services

The integration also exposes some services to control the box.

| Service name | Description | 
|---|---|
| set_brightness | Set brightness |
| set_syncmode | Set syncmode |
| set_intensity | Set intensity |
| set_entertainment_area | Set entertainment area |
| set_sync_state | Control all aspects of the syncbox state. Allows setting multiple paramters at once, e.g. intensity and syncmode |

For the most up-to-date list and parameter descriptions use the Services tab in the Developer tools and search for `huesyncbox` in the services list.

## Known issues

There have been reports where Home Assistant was not able to find the Philips Hue Play HDMI Sync Box automatically.
It is unclear why it happens for some people. So far I have not been able to reproduce it which makes solving it hard.

However it is now possible to add the syncbox manually through the "Add Integration" button where you can input the IP and ID of the box.

In case manual addition also does not work here are some workarounds that have been reported to work.

* Powercycling the Philips Hue Play HDMI Sync Box and/or restart Home Assistant and give it some time (say half an hour).
* Add `huesyncbox:` to the `configuration.yaml` file as was needed for HA versions <= 0.114.0. This should not work, but it is what users report...


## Installation

Make sure the Philips Hue Play HDMI Sync Box has been setup with the official Hue Sync app before adding it to Home Assistant.

### HACS (recommended)

* Install the integration from within HACS (you can use the search box to find it)
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen

### Manually (when not using HACS)

* Install the custom component
  * Downloading the zip from the releases section
  * Unzip it
  * Copy it to the custom_components directory of your Home Assistnat install as usual
* Restart Home Assistant
* Devices will be found automatically or can be added manually from the Home Assistant integrations screen
