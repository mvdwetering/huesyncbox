"""The Philips Hue Play HDMI Sync Box integration."""
import aiohuesyncbox
import async_timeout

from homeassistant.components import automation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import (
    entity_registry,
)
from homeassistant.helpers import issue_registry

from .services import async_register_services, async_unregister_services

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

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.api.close()

        if len(hass.data[DOMAIN]) == 0:
            hass.data.pop(DOMAIN)
            await async_unregister_services(hass)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    # Best effort cleanup. User might not even have the device anymore or had it factory reset.
    # Note that the entry already has been unloaded, so need to create API again
    try:
        async with async_timeout.timeout(10):
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

    automations_with_entity = []
    for entity in entities:
        if entity.domain == Platform.MEDIA_PLAYER:
            registry.async_remove(entity.entity_id)

            automations_with_entity = automation.automations_with_entity(
                hass, entity.entity_id
            )

            automation_info = []
            for automation_with_entity in automations_with_entity:
                if automation_entry := registry.async_get(automation_with_entity):
                    automation_info.append(
                        f"{automation_entry.name or automation_entry.original_name} ({automation_with_entity})\n"
                    )

            if len(automation_info) > 0:
                issue_registry.async_create_issue(
                    hass,
                    DOMAIN,
                    f"automations_using_deleted_mediaplayer_{config_entry.entry_id}",
                    is_fixable=True,
                    is_persistent=True,
                    severity=issue_registry.IssueSeverity.WARNING,
                    translation_key="automations_using_deleted_mediaplayer",
                    translation_placeholders={
                        "automations": ",".join(automation_info),
                        "media_player_entity": entity.entity_id,
                    },
                )

    config_entry.version = 2
    hass.config_entries.async_update_entry(config_entry)
