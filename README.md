# Philips Hue Play HDMI Sync Box

Minimum required Home Assistant version is: 2025.12.0

[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

- [About](#about)
- [Supported devices](#supported-devices)
- [Possible use-cases](#possible-use-cases)
- [Entities](#entities)
  - [Behavior](#behavior)
- [Data updates](#data-updates)
- [Actions](#actions)
  - [Set bridge](#set-bridge)
  - [Set sync state](#set-sync-state)
- [Installation](#installation)
- [Removal](#removal)
- [Updating from before version 2.0](#updating-from-before-version-20)

## About

> Please set up the Philips Hue Play HDMI Sync Box with the Hue App first and make sure it works before setting up this integration.

This integration allows you to control and automate your Philips Hue Play HDMI Sync Box from Home Assistant. Use it in automations, dashboards, and scripts to improve your entertainment experience.

## Supported devices

Both the 4K and 8K models are supported.

## Possible use-cases

- Start light syncing in specific cases (e.g., when a specific app is running, or only after dark)
- Turn the box on and control the selected input based on which devices are on (useful if the automatic switching can not be used)
- Automate actions when light syncing starts (e.g., dim other lights, close blinds)

## Entities

Entities are created for the following features:

- Power on/off
- Light sync on/off
- Intensity selection (subtle/moderate/high/intense)
- Sync mode selection (video/music/game)
- HDMI Input selection
- Brightness control slider
- Entertainment area selection
- HDMI input connection status
- Dolby Vision compatibility on/off (only on 4K)
- LED indicator mode selection
- Bridge connection status ⁺
- Bridge ID sensor ⁺
- IP address sensor ⁺
- Wifi quality sensor ⁺
- Content info sensor ⁺

Entities marked with ⁺ are disabled by default.

### Behavior

A few notes on behavior when changing entities. This behavior is just how the box reacts when sending these commands, not something explicitly coded in this integration.

- Enabling light sync will also power on the box
- Setting sync mode will also power on the box and start light sync on the selected mode
- When changing multiple entities the order is important. For example, Intensity applies to the current selected mode. So if you want to change both the `intensity` and `mode` you _first_ have to change the mode and then set the intensity. Otherwise, the intensity is applied to the "old" mode. To avoid ordering issues use the [`set_sync_state` action](#set-sync-state) which will take care of the ordering and is more efficient than sending everything separately.

## Data updates

This integration polls the Philips Hue Play HDMI Sync Box every 3 seconds.

## Actions

The integration exposes two additional actions.

### Set bridge

This action allows setting the bridge to be used by the Philips Hue Play HDMI Sync Box. For example when you have 2 different bridges you want to sync to and need to switch.

Note that changing the bridge by the box takes a while (about 15 seconds it seems). After the bridge has changed you might need to (re)select the `entertainment_area` if connectionstate is `invalidgroup` instead of `connected`.

| Parameter | Description | Example |
| --- | --- | --- |
| device_id | Home Assistant device ID of the Philips Hue Play HDMI Sync Box. | 11223344556677889900aabbccddeeff |
| bridge_id | ID of the bridge. A hexadecimal code of 16 characters. | 001788FFFE000000 |
| bridge_username | Username (a.k.a. application key) valid for the bridge. A long code of random characters. | abcdefghijklmnopqrstuvwxyz1234567890ABCD |
| bridge_clientkey | Client key that belongs with the username. A hexadecimal code of 32 characters. | 00112233445566778899AABBCCDDEEFF |

YAML action call example:

```yaml
action: huesyncbox.set_bridge
data:
  device_id: 11223344556677889900aabbccddeeff
  bridge_id: 001788FFFE000000
  bridge_username: abcdefghijklmnopqrstuvwxyz1234567890ABCD
  bridge_clientkey: 00112233445566778899AABBCCDDEEFF
```

### Set sync state

Set the state of multiple entities of the Philips Hue Play HDMI Sync Box at once. Using this action makes sure everything is set in the correct order and is more efficient than using separate commands.

| Parameter | Description | Example |
| --- | --- | --- |
| `device_id` | Home Assistant device ID of the Philips Hue Play HDMI Sync Box. | 11223344556677889900aabbccddeeff |
| `power` | Turn the box on or off. | true |
| `sync` | Set light sync state on or off. Setting this to on will also turn on the box. | true |
| `brightness` | Brightness value to set. | 42 |
| `intensity` | Intensity to set. | high |
| `mode` | Mode to set. Setting the mode will also turn on the box and start light sync. | video |
| `input` | Input to select. | input1 |
| `entertainment_area` | Entertainment area to select. Name must match _exactly_. | TV Area |

YAML action call example:

```yaml
action: huesyncbox.set_sync_state
data:
  device_id: 11223344556677889900aabbccddeeff
  power: true
  sync: true
  brightness: 42
  intensity: high
  mode: video
  input: input1
  entertainment_area: "TV Area"
```

## Installation

> **Note**
> Please set up the Philips Hue Play HDMI Sync Box with the Hue App first and make sure it works before setting up this integration.


### Downloading

#### Home Assistant Community Store (HACS)

> HACS is a third-party downloader for Home Assistant to easily install and update custom integrations made by the community. See <https://hacs.xyz/> for more details.

You can add this repository to HACS on your Home Assistant instance with the button below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mvdwetering&repository=huesyncbox&category=integration)

If the button does not work, or you don't want to use it, follow these steps to add the integration to HACS manually.

<details>
<summary>Manual HACS configuration steps</summary>

- Go to your Home Assistant instance
- Open the HACS page
- Search for "Philips Hue HDMI Sync Box" in the HACS search bar
- Click/tap on the integration to open the integration page
- Press the Download button to download the integration
- **Restart Home Assistant**

</details>

#### Manual download

- Go to the [releases section on GitHub](https://github.com/mvdwetering/huesyncbox/releases)
- Download the zip file for the version you want to install
- Extract the zip
- Ensure the `config/custom_components/huesyncbox` directory exists (create it if needed)
- Copy the files from the zip into the `config/custom_components/huesyncbox` directory
- **Restart Home Assistant**

### Configuration

The Philips Hue Play HDMI Sync Box will be discovered automatically in most cases. If not, add it manually via `Settings > Devices and Services` in Home Assistant.

For manual configuration, provide the following parameters (found in the Hue app's sync box device settings):

**IP Address**
: IP address of the device e.g. 192.168.1.123.

**Identifier**
: The device identifier of the box e.g. C42996000000

## Removal

This integration follows standard integration removal. No extra steps are required.

Go to "Settings > Devices & Services". Select Philips Hue Play HDMI Sync Box. Click the three dots ⋮ menu and then select Delete.

## Updating from before version 2.0

Version 2.0 is a complete rewrite, enabling multiple entities and modernizing the integration. It is a breaking change, but no functionality is lost—features have just moved.

See the [release notes for 2.0.0](https://github.com/mvdwetering/huesyncbox/releases/tag/v2.0.0) for migration details.
