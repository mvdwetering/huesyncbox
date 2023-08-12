"""The Philips Hue Play HDMI Sync Box integration."""
import aiohuesyncbox
import async_timeout
import voluptuous as vol  # type: ignore

from homeassistant.components import automation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryError
from homeassistant.helpers import (
    config_validation as cv,
    entity_registry,
)
from homeassistant.helpers.config_validation import make_entity_service_schema
from homeassistant.helpers.service import async_extract_config_entry_ids
from homeassistant.helpers import issue_registry

from .const import (
    ATTR_BRIDGE_CLIENTKEY,
    ATTR_BRIDGE_ID,
    ATTR_BRIDGE_USERNAME,
    DOMAIN,
    LOGGER,
    SERVICE_SET_BRIDGE,
)
from .coordinator import HueSyncBoxCoordinator
from .helpers import update_device_registry

PLATFORMS: list[Platform] = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


HUESYNCBOX_SET_BRIDGE_SCHEMA = make_entity_service_schema(
    {
        vol.Required(ATTR_BRIDGE_ID): cv.string,
        vol.Required(ATTR_BRIDGE_USERNAME): cv.string,
        vol.Required(ATTR_BRIDGE_CLIENTKEY): cv.string,
    }
)


async def async_register_services(hass: HomeAssistant):
    async def async_set_bridge(call):
        """
        Set bridge, note that this change is not instant.
        After calling you will have to wait until the `bridge_unique_id` matches the new bridge id
        and the bridge_connection_state is `connected`, `invalidgroup` or `streaming`, other status means it is connecting.
        I have seen the bridge change to take around 15 seconds.
        """

        config_entry_ids = await async_extract_config_entry_ids(hass, call)
        for config_entry_id in config_entry_ids:
            coordinator = hass.data[DOMAIN][config_entry_id]

            bridge_id = call.data.get(ATTR_BRIDGE_ID)
            username = call.data.get(ATTR_BRIDGE_USERNAME)
            clientkey = call.data.get(ATTR_BRIDGE_CLIENTKEY)

            await coordinator.api.hue.set_bridge(bridge_id, username, clientkey)

    if not hass.services.has_service(DOMAIN, SERVICE_SET_BRIDGE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_BRIDGE,
            async_set_bridge,
            schema=HUESYNCBOX_SET_BRIDGE_SCHEMA,
        )


async def async_unregister_services(hass: HomeAssistant):
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIDGE)


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
        raise ConfigEntryError(err) from err
    finally:
        if not initialized:
            await api.close()

    await update_device_registry(hass, entry, api)

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

            automations_with_entity = automation.automations_with_entity(hass, entity.entity_id)

            automation_info = []
            for automation_with_entity in automations_with_entity:
                if automation_entry := registry.async_get(automation_with_entity):
                    automation_info.append(f"{automation_entry.name or automation_entry.original_name} ({automation_with_entity})\n")

            if len(automation_info) > 0:
                issue_registry.async_create_issue(
                    hass,
                    DOMAIN,
                    f"automations_using_deleted_mediaplayer_{config_entry.entry_id}",
                    is_fixable=True,
                    is_persistent=True,
                    severity=issue_registry.IssueSeverity.WARNING,
                    translation_key="automations_using_deleted_mediaplayer",
                    translation_placeholders={"automations": ",".join(automation_info), "media_player_entity": entity.entity_id }
                )

    config_entry.version = 2
    hass.config_entries.async_update_entry(config_entry)
