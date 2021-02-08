"""Low-level functions for making requests to MLHub API endpoints."""

import itertools as it
from pathlib import Path
from typing import Iterator, List
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import urllib.parse

from requests.exceptions import HTTPError

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    # Handles this issue: https://github.com/tqdm/tqdm/issues/1082
    from tqdm import tqdm  # type: ignore [no-redef]

from .session import get_session
from .exceptions import EntityDoesNotExist, MLHubException


def _download(
        url: str,
        output_dir: Path,
        *,
        overwrite: bool = False,
        exist_okay: bool = True,
        chunk_size=5000000,
        **session_kwargs
) -> Path:
    """Internal function used to parallelize downloads from a given URL.

    Parameters
    ----------
    url : str
        This can either be a full URL or a path relative to the Radiant MLHub root URL.
    output_dir : Path
        Path to a local directory to which the file will be downloaded. File name will be generated
        automatically based on the download URL.
    overwrite : bool, optional
        Whether to overwrite an existing file at the same output location. Defaults to ``False``.
    exist_okay : bool, optional
        If ``True`` then the download will be skipped if an existing file of the same name is found, otherwise raises
        a :exc:`FileExistsError` exception. Defaults to ``True``.
    chunk_size : int, optional
        The size of byte range for each concurrent request.
    session_kwargs
        Keyword arguments passed directly to ``get_session``

    Returns
    -------
    output_path : Path
        The path to the downloaded file.

    Raises
    ------
    FileExistsError
        If file of the same name already exists in ``output_dir`` and ``exist_okay=False``.
    """

    def _get_ranges(total_size, interval):
        """Internal function for getting byte ranges from a total size and interval/chunk size."""
        start = 0
        while True:
            end = min(start + interval - 1, total_size)
            yield f'{start}-{end}'
            start += interval
            if start >= total_size:
                break

    def _fetch_range(url_, range_):
        """Internal function for fetching a byte range from the url."""
        return session.get(url_, headers={'Range': f'bytes={range_}'}).content

    # Create a session
    session = get_session(**session_kwargs)

    # HEAD the endpoint and follow redirects to get the actual download URL and Content-Length
    r = session.head(url, allow_redirects=True)
    r.raise_for_status()
    content_length = int(r.headers['Content-Length'])
    download_url = r.url

    # Resolve user directory shortcuts and relative paths
    output_dir = Path(output_dir).expanduser().resolve()

    # Get the full file path
    output_file_name = urllib.parse.urlsplit(download_url).path.rsplit('/', 1)[1]
    output_path = output_dir / output_file_name

    # Check for existing output file
    if output_path.exists():
        if exist_okay and not overwrite:
            return output_path
        elif not overwrite:
            raise FileExistsError(f'File {output_path} already exists and exist_okay=False. '
                                  f'Use exist_okay=True to skip downloading this file, or remove the existing file.')

    # Create the parent directory, if it does not exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Check that the endpoint accepts byte range requests
    use_range = r.headers.get('Accept-Ranges') == 'bytes'

    if use_range:
        # If we can use range requests, make concurrent requests to the byte ranges we need...
        with ThreadPoolExecutor(max_workers=20) as executor:
            with output_path.open('wb') as dst:
                with tqdm(total=round(content_length / 1000000., 1), unit='M') as pbar:
                    for chunk in executor.map(partial(_fetch_range, download_url), _get_ranges(content_length, chunk_size)):
                        dst.write(chunk)
                        pbar.update(round(chunk_size / 1000000., 1))
    else:
        # ...if not, stream the response
        with session.get(url, stream=True, allow_redirects=True) as r:
            with output_path.open('wb') as dst:
                with tqdm(total=round(content_length / 1000000., 1), unit='M') as pbar:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        dst.write(chunk)
                        pbar.update(round(chunk_size / 1000000., 1))

    return output_path


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
            raise EntityDoesNotExist(f'Dataset "{dataset_id}" does not exist.') from None
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
            raise EntityDoesNotExist(f'Collection "{collection_id}" does not exist.') from None
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
        raise EntityDoesNotExist(f'Collection "{collection_id}" does not exist.')
    raise MLHubException(f'An unknown error occurred: {response.status_code} ({response.reason})')


def download_archive(
        archive_id: str,
        output_dir: Path = None,
        *,
        overwrite: bool = False,
        exist_okay: bool = True,
        **session_kwargs
) -> Path:
    """Downloads the archive with the given ID to an output location (current working directory by default).

    Parameters
    ----------
    archive_id : str
        The ID of the archive to download.
    output_dir : Path
        Path to which the archive will be downloaded. Defaults to the current working directory.
    overwrite : bool, optional
        Whether to overwrite an existing archive at the same location. Defaults to ``False``.
    exist_okay : bool, optional
        If ``True`` then the download will be skipped if an existing file of the same name is found, otherwise raises
        a :exc:`FileExistsError` exception. Defaults to ``True``.
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    output_path : Path
        The path to the downloaded archive file.

    Raises
    ------
    FileExistsError
        If file at ``output_path`` already exists and both ``exist_okay`` and ``overwrite`` are ``False``.
    """
    output_dir = output_dir if output_dir is not None else Path.cwd()

    try:
        return _download(f'archive/{archive_id}', output_dir=output_dir, overwrite=overwrite, exist_okay=exist_okay, **session_kwargs)
    except HTTPError as e:
        if e.response.status_code != 404:
            raise
        raise EntityDoesNotExist(f'Archive "{archive_id}" does not exist and may still be generating. Please try again later.') from None
