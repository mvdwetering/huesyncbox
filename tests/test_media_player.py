"""Test mediaplayer."""

# import pytest

from typing import NamedTuple
from unittest.mock import MagicMock, Mock
from pytest_homeassistant_custom_component.common import AsyncMock

from custom_components.huesyncbox.media_player import HueSyncBoxMediaPlayerEntity
import aiohuesyncbox


class HueGroup(NamedTuple):
    name: str
    id: str
    active: bool


class HueInput(NamedTuple):
    id: str
    name: str
    type: str
    status: str
    last_sync_mode: str


async def test_device_state_attributes():
    """Test devicestate attribute values."""
    # PhilipsHuePlayHdmiSyncBox
    hsb = AsyncMock()
    mpe = HueSyncBoxMediaPlayerEntity(hsb)

    # No bridge connected
    hsb.api.execution.mode = "powersave"
    hsb.api.execution.hue_target = ""
    hsb.api.hue.groups = []

    assert {
        "mode": "powersave",
        "entertainment_area_list": [],
        "entertainment_area": None,
    } == mpe.device_state_attributes

    # Multiple groups
    hsb.api.execution.hue_target = "groups/id2"
    hsb.api.hue.groups = [
        HueGroup(name="A", id="id1", active=False),
        HueGroup(name="B", id="id2", active=False),
    ]

    assert {
        "mode": "powersave",
        "entertainment_area_list": ["A", "B"],
        "entertainment_area": "B",
    } == mpe.device_state_attributes


async def test_device_state_attributes_hdmi_status():
    """Test devicestate attribute values."""
    hsb = AsyncMock()
    mpe = HueSyncBoxMediaPlayerEntity(hsb)

    # API setup
    hsb.api.execution.mode = "powersave"
    hsb.api.execution.hue_target = ""
    hsb.api.hdmi.inputs = [
        HueInput(id="a", name="A", type="1", status="unplugged", last_sync_mode="game"),
        HueInput(id="b", name="B", type="2", status="plugged", last_sync_mode="video"),
        HueInput(id="c", name="C", type="3", status="linked", last_sync_mode="music"),
    ]

    attributes = mpe.device_state_attributes
    assert attributes["hdmi1_status"] == "unplugged"
    assert attributes["hdmi2_status"] == "plugged"
    assert attributes["hdmi3_status"] == "linked"


async def test_id_formats():
    """Test devicestate attribute values."""
    # Old format
    assert HueSyncBoxMediaPlayerEntity.get_hue_target_from_id("1") == "groups/1"
    # New format
    assert (
        HueSyncBoxMediaPlayerEntity.get_hue_target_from_id(
            "47XX285f-XXXX-492e-XXXX-51bXXXXa590c"
        )
        == "47XX285f-XXXX-492e-XXXX-51bXXXXa590c"
    )
