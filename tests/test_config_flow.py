"""Test the Philips Hue Play HDMI Sync Box config flow."""
from unittest.mock import MagicMock, Mock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.huesyncbox.config_flow import CannotConnect, InvalidAuth
from custom_components.huesyncbox.const import DOMAIN

import aiohuesyncbox


async def test_user_happy_flow(hass: HomeAssistant) -> None:
    """Test complete happyflow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "aiohuesyncbox.HueSyncBox",
    ) as huesyncbox_api, patch(
        "custom_components.huesyncbox.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        # __aenter__ stuff needed because used as context manager
        huesyncbox_api.return_value.__aenter__.return_value.device.name = "HueSyncBoxName"
        huesyncbox_api.return_value.__aenter__.return_value.register.return_value = {
                "registration_id": "registrationId",
                "access_token": "accessToken",
            }
        
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )
        await hass.async_block_till_done()

        assert result2["type"] == FlowResultType.SHOW_PROGRESS
        assert result2["step_id"] == "link"
        assert result2["progress_action"] == "wait_for_button"


        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "HueSyncBoxName"
    assert result2["data"] == {
        "host": "1.1.1.1",
        "unique_id": "test-unique_id",
        "access_token": "accessToken",
        "registration_id": "registrationId",
        "port" : 443,
        "path" : "/api",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "aiohuesyncbox.HueSyncBox.is_registered",
        return_value=False,
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
        "aiohuesyncbox.HueSyncBox.is_registered",
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
