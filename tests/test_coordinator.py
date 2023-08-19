from unittest.mock import Mock
import aiohuesyncbox
import pytest
from custom_components import huesyncbox
from custom_components.huesyncbox.helpers import (
    LinearRangeConverter,
    get_group_from_area_name,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from .conftest import force_coordinator_update, setup_integration


async def test_update_device_registry_and_config_entry_on_name_change(
    hass: HomeAssistant, mock_api
):
    integration = await setup_integration(hass, mock_api)

    # Verify current name
    dr = device_registry.async_get(hass)
    device = dr.async_get_device(
        identifiers={
            (huesyncbox.DOMAIN, "unique_id")
        }
    )
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
    device = dr.async_get_device(
        identifiers={
            (huesyncbox.DOMAIN, "unique_id")
        }
    )
    assert device is not None
    assert device.name == "New name"

    config_entry = hass.config_entries.async_get_entry(integration.entry.entry_id)
    assert config_entry is not None
    assert config_entry.title == "New name"
