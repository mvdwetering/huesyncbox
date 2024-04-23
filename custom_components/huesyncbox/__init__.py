"""The Philips Hue Play HDMI Sync Box integration."""
import asyncio
import aiohuesyncbox

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    entity_registry,
)
from homeassistant.helpers import issue_registry
from homeassistant.helpers.typing import ConfigType

from .services import async_register_services

from .const import (
    DOMAIN,
    LOGGER,
)
from .coordinator import HueSyncBoxCoordinator
from .helpers import update_device_registry, update_config_entry_title

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Philips Hue Play HDMI Sync Box integration."""
    hass.data[DOMAIN] = {}
    await async_register_services(hass)
    return True
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Philips Hue Play HDMI Sync Box from a config entry."""

    api = aiohuesyncbox.HueSyncBox(
        entry.data["host"],
        entry.data["unique_id"],
        access_token=entry.data.get("access_token"),
        port=entry.data["port"],
        path=entry.data["path"],
    )

    initialized = False
    try:
        await api.initialize()
        initialized = True
    except aiohuesyncbox.Unauthorized as err:
        raise ConfigEntryAuthFailed(err) from err
    except aiohuesyncbox.RequestError as err:
        raise ConfigEntryNotReady(err) from err
    finally:
        if not initialized:
            await api.close()

    await update_device_registry(hass, entry, api)
    update_config_entry_title(hass, entry, api.device.name)

    coordinator = HueSyncBoxCoordinator(hass, api)

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Best effort cleanup. User might not even have the device anymore or had it factory reset.
    # Note that the entry already has been unloaded, so need to create API again
    try:
        async with asyncio.timeout(10):
            async with aiohuesyncbox.HueSyncBox(
                entry.data["host"],
                entry.data["unique_id"],
                access_token=entry.data.get("access_token"),
                port=entry.data["port"],
                path=entry.data["path"],
            ) as api:
                await api.unregister(entry.data["registration_id"])
    except Exception as e:
        LOGGER.info(
            "Removing registration from Philips Hue Play HDMI Sync Box failed: %s ", e
        )


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    from_version = config_entry.version
    LOGGER.debug("Migrating from version %s", from_version)

    if config_entry.version == 1:
        migrate_v1_to_v2(hass, config_entry)
    if config_entry.version == 2:
        if config_entry.minor_version == 1:
            migrate_v2_1_to_v2_2(hass, config_entry)

    LOGGER.info(
        "Migration of ConfigEntry from version %s to version %s successful",
        from_version,
        config_entry.version,
    )

    return True


def migrate_v1_to_v2(hass: HomeAssistant, config_entry: ConfigEntry):
    # Mediaplayer entities are obsolete
    # cleanup so the user does not have to
    registry = entity_registry.async_get(hass)
    entities = entity_registry.async_entries_for_config_entry(
        registry, config_entry.entry_id
    )

    for entity in entities:
        if entity.domain == Platform.MEDIA_PLAYER:
            registry.async_remove(entity.entity_id)

            # There used to be a repair created here
            # Removed due to adding dependency on automation

    config_entry.version = 2
    hass.config_entries.async_update_entry(config_entry)


def migrate_v2_1_to_v2_2(hass: HomeAssistant, config_entry: ConfigEntry):
    # Remove any pending repairs
    issue_registry.async_delete_issue(
        hass, DOMAIN, f"automations_using_deleted_mediaplayer_{config_entry.entry_id}"
    )

    config_entry.version = 2
    config_entry.minor_version = 2
    hass.config_entries.async_update_entry(config_entry)
