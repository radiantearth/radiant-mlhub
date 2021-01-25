"""Low-level functions for making requests to MLHub API endpoints."""

from typing import Iterator
import itertools as it

from .session import get_session


def list_collections(**session_kwargs) -> Iterator[dict]:
    """Yields JSON-like dictionaries representing the paginated response bodies from the Radiant MLHub ``GET /collections`` endpoint.

    See the `MLHub API docs <https://docs.mlhub.earth/#radiant-mlhub-api>`_ for details.

    Parameters
    ----------
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Yields
    -------
    page : dict
    """
    session = get_session(**session_kwargs)
    yield from session.paginate('collections')


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
    return session.get(f'collections/{collection_id}').json()


def list_collection_items(
        collection_id: str,
        *,
        page_size: int = None,
        extensions: List[str] = None,
        limit: int = 100,
        **session_kwargs
) -> Iterator[dict]:
    """Yields JSON-like dictionaries representing STAC Item objects returned by the Radiant MLHub ``GET /collections/{collection_id}/items``
    endpoint.

    .. note::

        Because some collections may contain hundreds of thousands of items, this function limits the total number of responses
        to ``100`` by default. You can change this value using the ``limit`` keyword argument, but be aware that trying to list all items
        in a large collection may take a *very* long time.

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
        The maximum *total* number of items to yield. Defaults to ``100``.
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
            yield from page['items']

    yield from it.islice(_list_items(), limit)
