"""
Methods and classes to simplify requests to the MLHub API.
"""
import os
import configparser
from pathlib import Path
import functools
import urllib.parse
import platform
from typing import Optional

import requests

from .__version__ import __version__


class Session(requests.Session):
    """Custom class inheriting from :class:`requests.Session` with some additional conveniences:

    * Adds the API key as a ``key`` query parameter
    * Adds an ``Accept: application/json`` header
    * Adds a ``User-Agent`` header that contains the package name and version, plus system information
    * Prepends the MLHub root URL (``https://api.radiant.earth/mlhub/v1/``) to any request paths without a domain
    """

    API_KEY_ENV_VARIABLE = 'MLHUB_API_KEY'
    PROFILE_ENV_VARIABLE = 'MLHUB_PROFILE'
    ROOT_URL = 'https://api.radiant.earth/mlhub/v1/'

    def __init__(self, *, api_key: str):
        super().__init__()
        self.params.update({'key': api_key})
        self.headers.update({
            'Accept': 'application/json',
            # Add the package name + version and the system info to the user-agent header
            'User-Agent': f'{__name__.split(".")[0]}/{__version__} ({platform.version()})'
        })

    @functools.wraps(requests.Session.request)
    def request(self, method, url, **kwargs):
        """Overwrites the default :func:`requests.Session.request` method to prepend the MLHub root URL if the given
        ``url`` does not include a scheme.

        All arguments except ``url`` are passed directly to :func:`requests.Session.request`."""
        # Parse the url argument and substitute the base URL if this is a relative path
        parsed_url = urllib.parse.urlsplit(url)
        if not parsed_url.scheme:
            parsed_root = urllib.parse.urlsplit(self.ROOT_URL)
            url = urllib.parse.SplitResult(
                parsed_root.scheme,
                parsed_root.netloc,
                # Remove leading slashes so urljoin appends the path to our root path
                urllib.parse.urljoin(parsed_root.path, parsed_url.path.lstrip('/')),
                parsed_url.query,
                parsed_url.fragment,
            ).geturl()
        return super().request(method, url, **kwargs)

    @classmethod
    def from_env(cls) -> 'Session':
        """Create a session object from an API key from the environment variable.

        Returns
        -------
        session : Session

        Raises
        ------
        ValueError
            If the API key cannot be found in the environment
        """
        api_key = os.getenv(cls.API_KEY_ENV_VARIABLE)
        if not api_key:
            raise ValueError(f'No "{cls.API_KEY_ENV_VARIABLE}" variable found in environment.')
        return cls(api_key=api_key)

    @classmethod
    def from_config(cls, profile: Optional[str] = None) -> 'Session':
        """Create a session object by reading an API key from the given profile in the ``.mlhub/profiles`` file.

        Parameters
        ----------
        profile: str, optional
            The name of a profile configured in the ``.mlhub/profiles`` file.

        Returns
        -------
        session : Session

        Raises
        ------
        FileNotFoundError
            If the given config file does not exist.

        KeyError
            If the given profile cannot be found or there is no ``api_key`` property in the given profile section.
        """
        config_path = Path.home() / '.mlhub/profiles'
        if not config_path.exists():
            raise FileNotFoundError(f'No file found at {config_path}')

        config = configparser.ConfigParser()
        config.read(config_path)

        profile = profile or 'default'  # Use the default profile if the given profile is None or empty

        if profile not in config.sections():
            raise KeyError(f'Could not find "{profile}" section in {config_path}')
        api_key = config.get(profile, 'api_key', fallback=None)
        if not api_key:
            raise KeyError(f'Could not find "api_key" value in "{profile}" section of {config_path}')

        return cls(api_key=api_key)


def get_session(api_key: Optional[str] = None, profile: Optional[str] = None) -> Session:
    """Gets a :class:`Session` object that uses the given ``api_key`` for all requests. If no ``api_key`` argument is
    provided then the function will try to resolve an API key by finding the following values (in order of preference):

    1) An ``MLHUB_API_KEY`` environment variable
    2) A ``api_key`` value found in the given ``profile`` section of ``~/.mlhub/profiles``
    3) A ``api_key`` value found in the given ``default`` section of ``~/.mlhub/profiles``

    Parameters
    ----------
    api_key : str, optional
        The API key to use for all requests from the session. See description above for how the API key is resolved if not provided as an
        argument.
    profile: str, optional
            The name of a profile configured in the ``.mlhub/profiles`` file. This will be passed directly to :func:`~Session.from_config`.

    Returns
    -------
    session : Session

    Raises
    ------
    ValueError
        If no API key can be resolved.

    Examples
    --------
    >>> from radiant_mlhub import get_session
    # Get the API from the "default" profile
    >>> session = get_session()
    # Get the session from the "project1" profile
    # Alternatively, you could set the MLHUB_PROFILE environment variable to "project1"
    >>> session = get_session(profile='project1')
    # Pass an API key directly to the session
    # Alternatively, you could set the MLHUB_API_KEY environment variable to "some-api-key"
    >>> session = get_session(api_key='some-api-key')
    """

    if api_key:
        return Session(api_key=api_key)

    if Session.API_KEY_ENV_VARIABLE in os.environ:
        return Session.from_env()

    try:
        # Use the profile argument (if not None or empty), otherwise try to get the profile name from the MLHUB_PROFILE env variable.
        profile = profile or os.getenv(Session.PROFILE_ENV_VARIABLE)
        return Session.from_config(profile=profile)
    except (FileNotFoundError, KeyError):
        raise ValueError('Could not resolve an API key from arguments, the environment, or a config file.')