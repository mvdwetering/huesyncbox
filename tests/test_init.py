from unittest.mock import Mock, call, patch

import aiohuesyncbox
import pytest

from custom_components import huesyncbox
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.helpers import entity_registry, issue_registry, device_registry


from pytest_homeassistant_custom_component.common import MockConfigEntry  # type: ignore

from .conftest import setup_integration


async def test_device_info(hass: HomeAssistant, mock_api):
    integration = await setup_integration(hass, mock_api)

    dr = device_registry.async_get(hass)
    device = dr.async_get_device(identifiers={(huesyncbox.DOMAIN, "unique_id")})

    assert device is not None
    assert device.name == "Name"
    assert device.manufacturer == "Signify"
    assert device.model == "HSB1"
    assert device.sw_version == "firmwareversion"
    assert device.connections == {("mac", "unique_id")}


async def test_handle_authentication_error_during_setup(hass: HomeAssistant, mock_api):
    mock_api.initialize.side_effect = aiohuesyncbox.Unauthorized
    integration = await setup_integration(hass, mock_api)

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.state == ConfigEntryState.SETUP_ERROR
    assert config_entry.reason == "could not authenticate"

    assert mock_api.close.call_count == 1


async def test_handle_communication_error_during_setup(hass: HomeAssistant, mock_api):
    mock_api.initialize.side_effect = aiohuesyncbox.RequestError
    integration = await setup_integration(hass, mock_api)

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.state == ConfigEntryState.SETUP_RETRY

    assert mock_api.close.call_count == 1


async def test_unload_entry(hass: HomeAssistant, mock_api):
    integration = await setup_integration(hass, mock_api)

    # Unload first entry
    await hass.config_entries.async_unload(integration.entry.entry_id)
    await hass.async_block_till_done()

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.state == ConfigEntryState.NOT_LOADED

    assert mock_api.close.call_count == 1

    # Check data and services are still there
    assert huesyncbox.DOMAIN in hass.data
    assert hass.services.has_service(huesyncbox.DOMAIN, "set_bridge")
    assert hass.services.has_service(huesyncbox.DOMAIN, "set_sync_state")


@pytest.mark.parametrize(
    "side_effect",
    [
        (None),
        (aiohuesyncbox.AiohuesyncboxException),
    ],
)
async def test_remove_entry(hass: HomeAssistant, mock_api, side_effect):
    integration = await setup_integration(hass, mock_api)

    # Manually unload to be able to isolate remove call
    await hass.config_entries.async_unload(integration.entry.entry_id)
    await hass.async_block_till_done()

    with patch("aiohuesyncbox.HueSyncBox") as huesyncbox_api:
        # __aenter__ stuff needed because used as context manager
        mock_api_in_with_block = huesyncbox_api.return_value.__aenter__.return_value
        mock_api_in_with_block.unregister = Mock()
        mock_api_in_with_block.unregister.side_effect = side_effect

        await hass.config_entries.async_remove(integration.entry.entry_id)
        await hass.async_block_till_done()

        assert mock_api_in_with_block.unregister.call_count == 1
        assert mock_api_in_with_block.unregister.call_args == call(
            "registration_id_value"
        )

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is None


async def test_migrate(hass: HomeAssistant, mock_api):
    # Create v1 entry
    mock_config_entry = MockConfigEntry(
        version=1,
        domain=huesyncbox.DOMAIN,
        entry_id="entry_id",
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host",
            CONF_UNIQUE_ID: "unique_id",
            CONF_PORT: 1234,
            CONF_PATH: "/api_path",
            CONF_ACCESS_TOKEN: "token",
            huesyncbox.const.REGISTRATION_ID: "registration_id_value",
        },
    )

    # Setup will trigger migration
    integration = await setup_integration(
        hass, mock_api, mock_config_entry=mock_config_entry
    )

    # Just check if updated to latest version
    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.version == 2
    assert config_entry.minor_version == 2


async def test_migrate_v1_to_v2(hass: HomeAssistant, mock_api):
    # Create v1 entry
    mock_config_entry = MockConfigEntry(
        version=1,
        domain=huesyncbox.DOMAIN,
        entry_id="entry_id",
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host",
            CONF_UNIQUE_ID: "unique_id",
            CONF_PORT: 1234,
            CONF_PATH: "/api_path",
            CONF_ACCESS_TOKEN: "token",
            huesyncbox.const.REGISTRATION_ID: "registration_id_value",
        },
    )
    mock_config_entry.add_to_hass(hass)

    # Create old mediaplayer
    er = entity_registry.async_get(hass)
    mp_entity = er.async_get_or_create(
        "media_player",
        huesyncbox.DOMAIN,
        "mediaplayer_unique_id",
        config_entry=mock_config_entry,
    )

    # Create autmation referencing old mediaplayer (reference check is mocked)
    er = entity_registry.async_get(hass)
    automation_entity = er.async_get_or_create(
        "automation",
        huesyncbox.DOMAIN,
        "automation_unique_id",
        original_name="original name",
    )

    # Manually trigger upgrade
    with patch(
        "homeassistant.components.automation.automations_with_entity",
        return_value=[automation_entity.entity_id],
    ):
        huesyncbox.migrate_v1_to_v2(hass, mock_config_entry)

    # Check results
    assert er.async_get(mp_entity.entity_id) is None


async def test_migrate_v2_1_to_v2_2(hass: HomeAssistant, mock_api):
    # Create v1 entry
    mock_config_entry = MockConfigEntry(
        version=2,
        domain=huesyncbox.DOMAIN,
        entry_id="entry_id",
        title="HUESYNCBOX TITLE",
        data={
            CONF_HOST: "host",
            CONF_UNIQUE_ID: "unique_id",
            CONF_PORT: 1234,
            CONF_PATH: "/api_path",
            CONF_ACCESS_TOKEN: "token",
            huesyncbox.const.REGISTRATION_ID: "registration_id_value",
        },
    )
    mock_config_entry.add_to_hass(hass)

    # Create old migration issue
    issue_registry.async_create_issue(
        hass,
        huesyncbox.DOMAIN,
        f"automations_using_deleted_mediaplayer_{mock_config_entry.entry_id}",
        is_fixable=True,
        is_persistent=True,
        severity=issue_registry.IssueSeverity.WARNING,
        translation_key="automations_using_deleted_mediaplayer",
    )
    ir = issue_registry.async_get(hass)
    assert (
        ir.async_get_issue(
            huesyncbox.DOMAIN,
            f"automations_using_deleted_mediaplayer_{mock_config_entry.entry_id}",
        )
        is not None
    )

    # Manually trigger upgrade
    huesyncbox.migrate_v2_1_to_v2_2(hass, mock_config_entry)

    # Check results
    assert (
        ir.async_get_issue(
            huesyncbox.DOMAIN,
            f"automations_using_deleted_mediaplayer_{mock_config_entry.entry_id}",
        )
        is None
    )