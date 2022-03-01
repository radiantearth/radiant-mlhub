import itertools as it
from typing import Any, Dict, Iterator, List, Optional, cast

from requests.exceptions import HTTPError

from ..exceptions import EntityDoesNotExist, MLHubException
from ..session import get_session


def list_collections(*, api_key: Optional[str] = None, profile: Optional[str] = None) -> List[Dict[str, Any]]:

    """Gets a list of JSON-like dictionaries representing STAC Collection objects returned by the Radiant MLHub ``GET /collections``
    endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Returns
    -------
    collections: List[dict]
        List of JSON-like dictionaries representing STAC Collection objects.
    """
    session = get_session(api_key=api_key, profile=profile)
    r = session.get('collections')
    return cast(List[Dict[str, Any]], r.json().get('collections', []))


def get_collection(collection_id: str, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /collections/{p1}`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    collection_id : str
        The ID of the collection to fetch
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Returns
    -------
    collection : dict

    Raises
    ------
    EntityDoesNotExist
        If a 404 response code is returned by the API
    MLHubException
        If any other response code is returned
    """
    session = get_session(api_key=api_key, profile=profile)

    try:
        return cast(Dict[str, Any], session.get(f'collections/{collection_id}').json())
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(f'Collection "{collection_id}" does not exist.') from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})') from None


def list_collection_items(
        collection_id: str,
        *,
        page_size: Optional[int] = None,
        extensions: Optional[List[str]] = None,
        limit: int = 10,
        api_key: Optional[str] = None,
        profile: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """Yields JSON-like dictionaries representing STAC Item objects returned by the Radiant MLHub ``GET /collections/{collection_id}/items``
    endpoint.

    .. note::

        Because some collections may contain hundreds of thousands of items, this function limits the total number of responses
        to ``10`` by default. You can change this value by increasing the value of the ``limit`` keyword argument,
        or setting it to ``None`` to list all items. **Be aware that trying to list all items in a large collection may take a very
        long time.**

    Parameters
    ----------
    collection_id : str
        The ID of the collection from which to fetch items
    page_size : int
        The number of items to return in each page. If set to ``None``, then this parameter will not be passed to the API and
        the default API value will be used (currently ``30``).
    extensions : list
        If provided, then only items that support all of the extensions listed will be returned.
    limit : int
        The maximum *total* number of items to yield. Defaults to ``10``.
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Yields
    ------
    item : dict
        JSON-like dictionary representing a STAC Item associated with the given collection.
    """
    session = get_session(api_key=api_key, profile=profile)

    def _list_items() -> Iterator[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if page_size is not None:
            params['limit'] = page_size
        if extensions is not None:
            params['extensions'] = extensions
        for page in session.paginate(f'collections/{collection_id}/items', params=params):
            yield from page['features']

    yield from it.islice(_list_items(), limit)


def get_collection_item(collection_id: str, item_id: str, api_key: Optional[str] = None, profile: Optional[str] = None) -> Dict[str, Any]:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /collections/{p1}/items/{p2}`` endpoint.

    Parameters
    ----------
    collection_id : str
        The ID of the Collection to which the Item belongs.
    item_id : str
        The ID of the Item.
    api_key : str
        An API key to use for this request. This will override an API key set in a profile on using
        an environment variable
    profile: str
        A profile to use when making this request.

    Returns
    -------
    item : dict
    """
    session = get_session(api_key=api_key, profile=profile)

    try:
        return cast(Dict[str, Any], session.get(f'collections/{collection_id}/items/{item_id}').json())
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(f'Collection "{collection_id}" and/or item {item_id} do not exist.')
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})')
