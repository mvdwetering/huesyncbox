"""Test the Philips Hue Play HDMI Sync Box config flow."""

import asyncio
from ipaddress import IPv4Address
from unittest import mock
from unittest.mock import Mock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, UnknownFlow
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
import pytest

import aiohuesyncbox
from custom_components import huesyncbox

from .conftest import setup_integration


async def test_user_new_box(hass: HomeAssistant, mock_api: Mock) -> None:
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"

    # Filling in correct data (at least it maches the schema)
    # it will start link phase which tries to connect to the API so setup up front
    with (
        patch("aiohuesyncbox.HueSyncBox") as huesyncbox_instance,
        patch(
            "custom_components.huesyncbox.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        # __aenter__ stuff needed because used as context manager
        huesyncbox_instance.return_value.__aenter__.return_value = mock_api

        mock_api.is_registered.return_value = False

        # First attempt button not pressed yet, second try return value
        mock_api.register.side_effect = [aiohuesyncbox.InvalidState, mock.DEFAULT]
        mock_api.register.return_value = {
            "registration_id": "registrationId",
            "access_token": "accessToken",
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "unique_id": "test_unique_id",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "link"
        assert result["progress_action"] == "wait_for_button"
        await hass.async_block_till_done()

        # Wait until press the button is done
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Name"
        assert result["data"] == {
            "host": "1.1.1.1",
            "unique_id": "test_unique_id",
            "access_token": "accessToken",
            "registration_id": "registrationId",
            "port": 443,
            "path": "/api",
        }
        assert len(mock_setup_entry.mock_calls) == 1

        # One config entry should be created
        entries = hass.config_entries.async_entries(huesyncbox.DOMAIN)
        assert len(entries) == 1
        assert entries[0].title == "Name"
        assert entries[0].unique_id == "test_unique_id"


async def test_reconfigure_host(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)
    assert integration.entry.data["host"] != "1.2.3.4"

    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": integration.entry.entry_id,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"

    # Provide different host for existing entry, should update
    with patch("aiohuesyncbox.HueSyncBox.is_registered", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.2.3.4",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.ABORT
        assert integration.entry.data["host"] == "1.2.3.4"


@pytest.mark.parametrize(
    ("side_effect", "error_message"),
    [
        (aiohuesyncbox.RequestError, "cannot_connect"),
        (Exception, "unknown"),
    ],
)
async def test_connection_errors_during_connection_check(
    hass: HomeAssistant, side_effect: type[Exception], error_message: str
) -> None:
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"

    with patch(
        "aiohuesyncbox.HueSyncBox.is_registered",
        return_value=False,
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure"
        assert result["errors"] == {"base": error_message}


@pytest.mark.parametrize(
    "side_effect",
    [
        (aiohuesyncbox.Unauthorized),
        (aiohuesyncbox.RequestError),
        (aiohuesyncbox.AiohuesyncboxException),
        (asyncio.InvalidStateError),
    ],
)
async def test_user_box_connection_errors_during_link(
    hass: HomeAssistant, mock_api: Mock, side_effect: type[Exception]
) -> None:
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"

    # Filling in correct data (at least it maches the schema)
    # it will start link phase which tries to connect to the API so setup up front
    with patch("aiohuesyncbox.HueSyncBox.__aenter__", return_value=mock_api):
        mock_api.is_registered.return_value = False
        mock_api.register.side_effect = side_effect

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "connection_failed"


# asyncio.CancelledError
async def test_user_box_abort_flow_during_link(
    hass: HomeAssistant, mock_api: Mock
) -> None:
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "configure"

    # Filling in correct data (at least it maches the schema)
    # it will start link phase which tries to connect to the API so setup up front
    with patch("aiohuesyncbox.HueSyncBox.__aenter__", return_value=mock_api):
        mock_api.is_registered.return_value = False
        mock_api.register.side_effect = aiohuesyncbox.InvalidState

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "1.1.1.1",
                "unique_id": "test-unique_id",
            },
        )

        assert result["type"] == FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "link"
        assert result["progress_action"] == "wait_for_button"

        hass.config_entries.flow.async_abort(result["flow_id"])
        with pytest.raises(UnknownFlow):
            hass.config_entries.flow.async_get(result["flow_id"])


async def test_zeroconf_new_box(hass: HomeAssistant, mock_api: Mock) -> None:
    # Triggered by discovery
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("1.2.3.4"),
            ip_addresses=[IPv4Address("1.2.3.4")],
            port=443,
            hostname="unique_id.local",
            type="_huesync._tcp.local.",
            name="HueSyncBox-UniqueId._huesync._tcp.local.",
            properties={
                "_raw": {
                    "path": b"/api",
                    "uniqueid": b"unique_id_value",
                    "devicetype": b"HSB001",
                    "name": b"Hue Syncbox Name",
                },
                "path": "/api",
                "uniqueid": "unique_id_value",
                "devicetype": "HSB001",
                "name": "Hue Syncbox Name",
            },
        ),
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    # Confirm discovery will start link phase which tries to
    # connect to the API so setup up front

    with (
        patch("aiohuesyncbox.HueSyncBox") as huesyncbox_instance,
        patch(
            "custom_components.huesyncbox.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        # __aenter__ stuff needed because used as context manager
        huesyncbox_instance.return_value.__aenter__.return_value = mock_api
        mock_api.register.return_value = {
            "registration_id": "registrationId",
            "access_token": "accessToken",
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

        assert result["type"] == FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "link"
        assert result["progress_action"] == "wait_for_button"
        await hass.async_block_till_done()

        # Wait until press the button is done
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Name"
        assert result["data"] == {
            "host": "1.2.3.4",
            "unique_id": "unique_id_value",
            "access_token": "accessToken",
            "registration_id": "registrationId",
            "port": 443,
            "path": "/api",
        }
        assert len(mock_setup_entry.mock_calls) == 1


async def test_zeroconf_already_configured(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)

    # Make sure there is different data befroe
    assert integration.entry.data["host"] != "1.2.3.4"
    assert integration.entry.data["port"] != 443
    assert integration.entry.data["path"] != "/different"

    # Trigger flow
    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("1.2.3.4"),
            ip_addresses=[IPv4Address("1.2.3.4")],
            port=443,
            hostname="unique_id.local",
            type="_huesync._tcp.local.",
            name="HueSyncBox-UniqueId._huesync._tcp.local.",
            properties={
                "_raw": {
                    "path": b"/api",
                    "uniqueid": b"unique_id_value",
                    "devicetype": b"HSB001",
                    "name": b"Hue Syncbox Name",
                },
                "path": "/different",
                "uniqueid": "123456ABCDEF",
                "devicetype": "HSB001",
                "name": "Hue Syncbox Name",
            },
        ),
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"

    assert integration.entry.data["host"] == "1.2.3.4"
    assert integration.entry.data["port"] == 443
    assert integration.entry.data["path"] == "/different"


async def test_reauth_flow(hass: HomeAssistant, mock_api: Mock) -> None:
    integration = await setup_integration(hass, mock_api)

    assert integration.entry.data["access_token"] == "token_value"  # noqa: S105
    assert integration.entry.data["registration_id"] == "registration_id_value"

    result = await hass.config_entries.flow.async_init(
        huesyncbox.DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": integration.entry.entry_id,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # Confirming will start link phase which tries to connect to the API so setup upfront
    with (
        patch("aiohuesyncbox.HueSyncBox") as huesyncbox_instance,
    ):
        huesyncbox_instance.return_value.__aenter__.return_value = mock_api

        # First attempt button not pressed yet, second try return value
        mock_api.register.return_value = {
            "registration_id": "NewRegistrationId",
            "access_token": "NewAccessToken",
        }

        # Press next on reauth confirm form
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "link"
        assert result["progress_action"] == "wait_for_button"
        await hass.async_block_till_done()

        # Wait until press the button is done
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"

        # Config entry token and registration id should be updated,
        assert integration.entry.data["access_token"] == "NewAccessToken"  # noqa: S105
        assert integration.entry.data["registration_id"] == "NewRegistrationId"
        # rest should still be the same
        assert integration.entry.data["host"] == "host_value"
        assert integration.entry.data["port"] == 1234
        assert integration.entry.data["unique_id"] == "unique_id_value"
        assert integration.entry.data["path"] == "/path_value"
