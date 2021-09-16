"""
Methods and classes to simplify constructing and authenticating requests to the MLHub API.

It is generally recommended that you use the :func:`get_session` function to create sessions, since this will propertly handle resolution
of the API key from function arguments, environment variables, and profiles as described in :ref:`Authentication`. See the
:func:`get_session` docs for usage examples.
"""

import configparser
import os
import platform
import urllib.parse
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

import requests
import requests.adapters
from urllib3.util import Retry

from .__version__ import __version__
from .exceptions import APIKeyNotFound, AuthenticationError

ANONYMOUS_PROFILE = "__anonymous__"


class Session(requests.Session):
    """Custom class inheriting from :class:`requests.Session` with some additional conveniences:

    * Adds the API key as a ``key`` query parameter
    * Adds an ``Accept: application/json`` header
    * Adds a ``User-Agent`` header that contains the package name and version, plus basic system information like the OS name
    * Prepends the MLHub root URL (``https://api.radiant.earth/mlhub/v1/``) to any request paths without a domain
    * Raises a :exc:`radiant_mlhub.exceptions.AuthenticationError` for ``401 (UNAUTHORIZED)`` responses
    * Calls :meth:`requests.Response.raise_for_status` after all requests to raise exceptions for any status codes above 400.
    """

    MLHUB_HOME_ENV_VARIABLE = 'MLHUB_HOME'
    API_KEY_ENV_VARIABLE = 'MLHUB_API_KEY'
    PROFILE_ENV_VARIABLE = 'MLHUB_PROFILE'
    ROOT_URL_ENV_VARIABLE = 'MLHUB_ROOT_URL'

    DEFAULT_ROOT_URL = 'https://api.radiant.earth/mlhub/v1/'

    def __init__(self, *, api_key: Optional[str]):
        super().__init__()

        self.root_url = os.getenv(self.ROOT_URL_ENV_VARIABLE, self.DEFAULT_ROOT_URL)

        # Add the API key query parameter
        if api_key is not None:
            self.params.update({'key': api_key})  # type: ignore [union-attr]

        # Set the default headers
        self.headers.update({
            'Accept': 'application/json',
            # Add the package name + version and the system info to the user-agent header
            'User-Agent': f'{__name__.split(".")[0]}/{__version__} ({platform.version()})'
        })

        # Configure retries
        retries = Retry(
            total=None,
            connect=5,
            backoff_factor=0.2
        )
        self.mount('https://', requests.adapters.HTTPAdapter(max_retries=retries))
        self.mount('http://', requests.adapters.HTTPAdapter(max_retries=retries))

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:  # type: ignore[override]
        """Overwrites the default :meth:`requests.Session.request` method to prepend the MLHub root URL if the given
        ``url`` does not include a scheme. This will raise an :exc:`~radiant_mlhub.exceptions.AuthenticationError` if a 401 response is
        returned by the server, and a :class:`~requests.exceptions.HTTPError` if any other status code of 400 or above is returned.

        Parameters
        ----------
        method : str
            The request method to use. Passed directly to the ``method`` argument of :meth:`requests.Session.request`
        url : str
            Either a full URL or a path relative to the :attr:`ROOT_URL`. For example, to make a request to the Radiant MLHub API
            ``/collections`` endpoint, you could use ``session.get('collections')``.
        **kwargs
            All other keyword arguments are passed directly to :meth:`requests.Session.request` (see that documentation for an explanation
            of these keyword arguments).

        Raises
        ------
        AuthenticationError
            If the response status code is 401

        HTTPError
            For all other response status codes at or above 400
        """
        # Parse the url argument and substitute the base URL if this is a relative path
        parsed_url = urllib.parse.urlsplit(url)
        if not parsed_url.scheme:
            parsed_root = urllib.parse.urlsplit(self.root_url)
            url = urllib.parse.SplitResult(
                parsed_root.scheme,
                parsed_root.netloc,
                # Remove leading slashes so urljoin appends the path to our root path
                urllib.parse.urljoin(parsed_root.path, parsed_url.path.lstrip('/')),
                parsed_url.query,
                parsed_url.fragment,
            ).geturl()

        response = super().request(method, url, **kwargs)

        # Handle authentication errors
        if response.status_code == 401:
            msg = "Authentication failed. "
            request_qs = str(urllib.parse.urlsplit(response.request.url).query)
            request_params = urllib.parse.parse_qs(request_qs)
            if "key" in request_params:
                msg += f"API Key: {request_params['key'][0]}"
            else:
                msg += "No API key provided."
            raise AuthenticationError(msg)

        # Raise exceptions for any HTTP codes >=400
        response.raise_for_status()

        return response

    @classmethod
    def from_env(cls) -> 'Session':
        """Create a session object from an API key from the environment variable.

        Returns
        -------
        session : Session

        Raises
        ------
        APIKeyNotFound
            If the API key cannot be found in the environment
        """
        api_key = os.getenv(cls.API_KEY_ENV_VARIABLE)
        if not api_key:
            raise APIKeyNotFound(f'No "{cls.API_KEY_ENV_VARIABLE}" variable found in environment.')
        return cls(api_key=api_key)

    @classmethod
    def from_config(cls, profile: Optional[str] = None) -> 'Session':
        """Create a session object by reading an API key from the given profile in the ``profiles`` file. By default,
        the client will look for the ``profiles`` file in a ``.mlhub`` directory in the user's home directory (as
        determined by :meth:`Path.home <pathlib.Path.home>`). However, if an ``MLHUB_HOME`` environment variable is
        present, the client will look in that directory instead.

        Parameters
        ----------
        profile: str, optional
            The name of a profile configured in the ``profiles`` file.

        Returns
        -------
        session : Session

        Raises
        ------
        APIKeyNotFound
            If the given config file does not exist, the given profile cannot be found, or there is no ``api_key`` property in the
            given profile section.
        """
        mlhub_home = Path(os.getenv(Session.MLHUB_HOME_ENV_VARIABLE, Path.home() / '.mlhub'))
        config_path = mlhub_home / 'profiles'
        if not config_path.exists():
            raise APIKeyNotFound(f'No file found at {config_path}')

        config = configparser.ConfigParser()
        config.read(config_path)

        profile = profile or 'default'  # Use the default profile if the given profile is None or empty

        if profile not in config.sections():
            raise APIKeyNotFound(f'Could not find "{profile}" section in {config_path}')
        api_key = config.get(profile, 'api_key', fallback=None)
        if not api_key:
            raise APIKeyNotFound(f'Could not find "api_key" value in "{profile}" section of {config_path}')

        return cls(api_key=api_key)

    def paginate(self, url: str, **kwargs: Any) -> Iterator[Dict[str, Any]]:
        """Makes a GET request to the given ``url`` and paginates through all results by looking for a link in each response with a
        ``rel`` type of ``"next"``. Any additional keyword arguments are passed directly to :meth:`requests.Session.get`.

        Parameters
        ----------
        url : str
            The URL to which the initial request will be made. Note that this may either be a full URL or a path relative to the
            :attr:`ROOT_URL` as described in :meth:`Session.request`.

        Yields
        ------
        page : dict
            An individual response as a dictionary.
        """
        current_url: Optional[str] = str(url)
        while True:
            if current_url is None:
                break
            page = self.get(current_url, **kwargs).json()
            yield page

            current_url = dict(next((
                link for link in page.get('links', [])
                if link['rel'] == 'next'), {}
            )).get('href')


def get_session(*, api_key: Optional[str] = None, profile: Optional[str] = None) -> Session:
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
    profile : str, optional
        The name of a profile configured in the ``.mlhub/profiles`` file. This will be passed directly to :func:`~Session.from_config`.

    Returns
    -------
    session : Session

    Raises
    ------
    APIKeyNotFound
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

        if profile == ANONYMOUS_PROFILE:
            # For the special case of the "__anonymous__" profile, create a Session with no API key
            return Session(api_key=None)

        return Session.from_config(profile=profile)
    except APIKeyNotFound:
        raise APIKeyNotFound('Could not resolve an API key from arguments, the environment, or a config file.') from None
