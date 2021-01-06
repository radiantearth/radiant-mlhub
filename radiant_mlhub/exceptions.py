class MLHubException(Exception):
    """Base exception class for all Radiant MLHub exceptions"""


class AuthenticationError(MLHubException):
    """Raised when the Radiant MLHub API cannot authenticate the request, either because the API key is invalid or expired, or because
    no API key was provided in the request."""
