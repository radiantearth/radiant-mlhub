"""Low-level functions for making requests to MLHub API endpoints."""

import itertools as it
from pathlib import Path
from typing import Iterator, Union, List

from requests.exceptions import HTTPError
from tqdm import tqdm

from .session import get_session
from .exceptions import EntityDoesNotExist, MLHubException


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
    try:
        return session.get(f'datasets/{dataset_id}').json()
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(dataset_id) from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})') from None


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

    Raises
    ------
    EntityDoesNotExist
        If a 404 response code is returned by the API
    MLHubException
        If any other response code is returned
    """
    session = get_session(**session_kwargs)

    try:
        return session.get(f'collections/{collection_id}').json()
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(collection_id) from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})') from None


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

    response = session.get(f'collections/{collection_id}/items/{item_id}')

    if response.ok:
        return response.json()
    if response.status_code == 404:
        raise EntityDoesNotExist(collection_id)
    raise MLHubException(f'An unknown error occurred: {response.status_code} ({response.reason})')


def download_archive(archive_id: str, output_path: Union[Path], overwrite: bool = False, **session_kwargs):
    """Downloads the archive with the given ID to an output location (current working directory by default).

    Parameters
    ----------
    archive_id : str
        The ID of the archive to download.
    output_path : Path
        Path to which the archive will be downloaded.
    overwrite : bool, optional
        Whether to overwrite an existing file of the same name. Defaults to ``False``.
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Raises
    ------
    FileExistsError
        If file at ``output_path`` already exists and ``overwrite==False``.
    """
    output_path = Path(output_path).expanduser().resolve()

    if output_path.exists() and not overwrite:
        raise FileExistsError(f'File {output_path} already exists. Use overwrite=True to overwrite this file.')

    session = get_session(**session_kwargs)

    r = session.get(f'archive/{archive_id}', stream=True)

    total_size = int(r.headers['Content-Length'])

    with output_path.open('wb') as dst:
        # TODO: Be more thoughtful about the chunksize
        with tqdm(total=total_size, leave=False) as pbar:
            chunk_size = 5000000
            for chunk in r.iter_content(chunk_size=chunk_size):
                dst.write(chunk)
                pbar.update(min(chunk_size, pbar.total - pbar.n))
