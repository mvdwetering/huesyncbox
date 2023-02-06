"""Test the Philips Hue Play HDMI Sync Box config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.huesyncbox.config_flow import CannotConnect, InvalidAuth
from custom_components.huesyncbox.const import DOMAIN

import aiohuesyncbox


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "aiohuesyncbox.HueSyncBox.initialize",
        # return_value=True,
    ), patch(
        "custom_components.huesyncbox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Name of the device"
    assert result2["data"] == {
        "ip_address": "1.1.1.1",
        "unique_id": "test-unique_id",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        # "aiohuesyncbox.HueSyncBox.is_registered",
        # return_value=False,
        "aiohuesyncbox.HueSyncBox.initialize",
        side_effect=aiohuesyncbox.Unauthorized,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        # "aiohuesyncbox.HueSyncBox.is_registered",
        "aiohuesyncbox.HueSyncBox.initialize",
        side_effect=aiohuesyncbox.RequestError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
