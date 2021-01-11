"""Low-level functions for making requests to MLHub API endpoints."""

from typing import Iterator

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
