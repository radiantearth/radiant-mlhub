"""Low-level functions for making requests to MLHub API endpoints."""

import itertools as it
from typing import Iterator, List

from .session import get_session
from .exceptions import CollectionDoesNotExist, MLHubException


def list_datasets(**session_kwargs) -> List[dict]:
    """Gets a list of JSON-like dictionaries representing dataset objects returned by the Radiant MLHub ``GET /datasets`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    datasets : List[dict]
    """
    session = get_session(**session_kwargs)
    return session.get('datasets').json()


def get_dataset(dataset_id: str, **session_kwargs) -> dict:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /datasets/{dataset_id}`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    dataset_id : str
        The ID of the dataset to fetch
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    dataset : dict
    """
    session = get_session(**session_kwargs)
    return session.get(f'datasets/{dataset_id}').json()


def list_collections(**session_kwargs) -> List[dict]:
    """Gets a list of JSON-like dictionaries representing STAC Collection objects returned by the Radiant MLHub ``GET /collections``
    endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------

    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    collections: List[dict]
        List of JSON-like dictionaries representing STAC Collection objects.
    """
    session = get_session(**session_kwargs)
    r = session.get('collections')
    return r.json().get('collections', [])


def get_collection(collection_id: str, **session_kwargs) -> dict:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /collections/{p1}`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    collection_id : str
        The ID of the collection to fetch
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    collection : dict
    """
    session = get_session(**session_kwargs)
    response = session.get(f'collections/{collection_id}')

    if response.ok:
        return response.json()
    if response.status_code == 404:
        raise CollectionDoesNotExist(collection_id)
    raise MLHubException(f'An unknown error occurred: {response.status_code} ({response.reason})')


def list_collection_items(
        collection_id: str,
        *,
        page_size: int = None,
        extensions: List[str] = None,
        limit: int = 10,
        **session_kwargs
) -> Iterator[dict]:
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
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Yields
    ------
    item : dict
        JSON-like dictionary representing a STAC Item associated with the given collection.
    """
    session = get_session(**session_kwargs)

    def _list_items():
        params = {}
        if page_size is not None:
            params['limit'] = page_size
        if extensions is not None:
            params['extensions'] = extensions
        for page in session.paginate(f'collections/{collection_id}/items', params=params):
            yield from page['features']

    yield from it.islice(_list_items(), limit)


def get_collection_item(collection_id: str, item_id: str, **session_kwargs) -> dict:
    """Returns a JSON-like dictionary representing the response from the Radiant MLHub ``GET /collections/{p1}/items/{p2}`` endpoint.

    Parameters
    ----------
    collection_id : str
        The ID of the Collection to which the Item belongs.
    item_id : str
        The ID of the Item.
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    item : dict
    """
    session = get_session(**session_kwargs)
    return session.get(f'collections/{collection_id}/items/{item_id}').json()
