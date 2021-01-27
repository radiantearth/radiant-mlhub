class MLHubException(Exception):
    """Base exception class for all Radiant MLHub exceptions"""


class AuthenticationError(MLHubException):
    """Raised when the Radiant MLHub API cannot authenticate the request, either because the API key is invalid or expired, or because
    no API key was provided in the request."""


class APIKeyNotFound(MLHubException):
    """Raised when an API key cannot be found using any of the strategies described in the :ref:`Authentication` docs."""


class EntityDoesNotExist(MLHubException):
    """Raised when attempting to fetch a collection that does not exist in the Radiant MLHub API."""
