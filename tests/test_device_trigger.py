"""The tests for Philips Hue Play HDMI Sync Box device triggers."""

import pytest

from homeassistant.components import automation
from custom_components.huesyncbox import DOMAIN

from homeassistant.helpers import device_registry
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    assert_lists_same,
    async_get_device_automations,
    async_mock_service,
    mock_device_registry,
    mock_registry,
)


@pytest.fixture
def device_reg(hass):
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


@pytest.fixture
def entity_reg(hass):
    """Return an empty, loaded, registry."""
    return mock_registry(hass)


@pytest.fixture
def calls(hass):
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "automation")


async def test_get_triggers(hass, device_reg, entity_reg):
    """Test we get the expected triggers from a dummy."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(device_registry.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_reg.async_get_or_create(DOMAIN, "test", "5678", device_id=device_entry.id)
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "hdmi1_status_changed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "hdmi2_status_changed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "hdmi3_status_changed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "hdmi4_status_changed",
            "device_id": device_entry.id,
            "entity_id": f"{DOMAIN}.test_5678",
        },
    ]
    triggers = await async_get_device_automations(hass, "trigger", device_entry.id)
    assert_lists_same(triggers, expected_triggers)


async def test_if_fires_on_state_change(hass, calls):
    """Test for hdmi#_status_changed triggers firing."""
    hass.states.async_set("dummy.entity", "STATE", {"hdmi3_status": "unplugged"})

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": "",
                        "entity_id": "dummy.entity",
                        "type": "hdmi3_status_changed",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": (
                                "hdmi3_status - {{ trigger.platform}} - "
                                "{{ trigger.entity_id}} - "
                                "{{ trigger.from_state.attributes.hdmi3_status}} - "
                                "{{ trigger.to_state.attributes.hdmi3_status}}"
                            )
                        },
                    },
                },
            ]
        },
    )

    # Fake that the hdmi status changed
    hass.states.async_set("dummy.entity", "STATE", {"hdmi3_status": "linked"})
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert (
        calls[0].data["some"]
        == "hdmi3_status - device - dummy.entity - unplugged - linked"
    )
