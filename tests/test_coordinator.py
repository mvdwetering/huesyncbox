import asyncio
from unittest.mock import Mock

import aiohuesyncbox
import pytest

from custom_components import huesyncbox
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from .conftest import force_coordinator_update, setup_integration


async def test_update_device_registry_and_config_entry_on_name_change(
    hass: HomeAssistant, mock_api
):
    integration = await setup_integration(hass, mock_api)

    # Verify current name
    dr = device_registry.async_get(hass)
    device = dr.async_get_device(identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")})
    assert device is not None
    assert device.name == "Name"

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.title == "Name"

    # Set new name and force update
    mock_api.device.name = "New name"
    mock_api.device.__eq__ = Mock()
    mock_api.device.__eq__.return_value = False
    await force_coordinator_update(hass)

    # Check device registry and config entry got updated
    device = dr.async_get_device(identifiers={(huesyncbox.DOMAIN, "123456ABCDEF")})
    assert device is not None
    assert device.name == "New name"

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.title == "New name"


async def test_authentication_error_starts_reauth_flow(hass: HomeAssistant, mock_api):
    integration = await setup_integration(hass, mock_api)

    # Make sure we start as expected
    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert len(list(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))) == 0

    # Trigger unauthorized update
    mock_api.update.side_effect = aiohuesyncbox.Unauthorized
    await force_coordinator_update(hass)

    # Check if reauth flow is started
    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert len(list(config_entry.async_get_active_flows(hass, {SOURCE_REAUTH}))) == 1


@pytest.mark.parametrize(
    "side_effect",
    [
        (aiohuesyncbox.RequestError),
        (asyncio.TimeoutError),
    ],
)
async def test_continued_communication_errors_mark_entities_unavailable(
    hass: HomeAssistant, mock_api, side_effect
):
    entity_under_test = "switch.name_power"
    await setup_integration(hass, mock_api)

    # Make sure we start as expected
    entity = hass.states.get(entity_under_test)
    assert entity is not None
    assert entity.state == "on"

    # Setup communication error
    mock_api.update.side_effect = side_effect

    # Trigger 4 updates, entities should be fine
    for _ in range(4):
        await force_coordinator_update(hass)
        entity = hass.states.get(entity_under_test)
        assert entity.state == "on"

    # 5th error makes entity unavailable
    await force_coordinator_update(hass)
    entity = hass.states.get(entity_under_test)
    assert entity.state == "unavailable"
