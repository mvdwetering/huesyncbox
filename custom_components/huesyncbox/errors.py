"""Errors for the HueSyncBox component."""
from homeassistant.exceptions import HomeAssistantError


class HueSyncBoxException(HomeAssistantError):
    """Base class for HueSyncBox exceptions."""


class CannotConnect(HueSyncBoxException):
    """Unable to connect to the syncbox."""


class AuthenticationRequired(HueSyncBoxException):
    """Unknown error occurred."""
