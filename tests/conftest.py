"""Test helpers for Philips Hue Play HDMI Sync Box."""
import pytest
from pytest_homeassistant_custom_component.async_mock import AsyncMock, Mock


@pytest.fixture
def mock_api(hass):
    """Mock the Philips Hue Play HDMI Sync Box api."""
    api = Mock(
        initialize=AsyncMock(return_value={""}), register=AsyncMock(), close=AsyncMock()
    )
    api.mock_requests = []

    async def mock_request(method, path, **kwargs):
        kwargs["method"] = method
        kwargs["path"] = path
        api.mock_requests.append(kwargs)

        return None

    return api
