"""Common fixtures  for the Philips Hue Play HDMI Sync Box integration tests."""

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations"""
    yield