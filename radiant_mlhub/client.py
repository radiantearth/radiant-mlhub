"""Low-level functions for making requests to MLHub API endpoints."""

import itertools as it
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Iterator, List

from requests.exceptions import HTTPError

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    # Handles this issue: https://github.com/tqdm/tqdm/issues/1082
    from tqdm import tqdm  # type: ignore [no-redef]

from .exceptions import EntityDoesNotExist, MLHubException
from .session import get_session


def _download(
        url: str,
        output_dir: Path,
        *,
        if_exists: str = 'resume',
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
    if_exists : str, optional
        How to handle an existing archive at the same location. If ``"skip"``, the download will be skipped. If ``"overwrite"``,
        the existing file will be overwritten and the entire file will be re-downloaded. If ``"resume"`` (the default), the
        existing file size will be compared to the size of the download (using the ``Content-Length`` header). If the existing
        file is smaller, then only the remaining portion will be downloaded. Otherwise, the download will be skipped.
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
    ValueError
        If ``if_exists`` is not one of ``"skip"``, ``"overwrite"``, or ``"resume"``.
    """
    if if_exists not in {'skip', 'overwrite', 'resume'}:
        raise ValueError('if_exists must be one of "skip", "overwrite", or "resume"')

    def _get_ranges(total_size, interval, start=0):
        """Internal function for getting byte ranges from a total size and interval/chunk size."""
        while True:
            end = min(start + interval - 1, total_size)
            yield f'{start}-{end}'
            start += interval
            if start >= total_size:
                break

    def _fetch_range(url_, range_):
        """Internal function for fetching a byte range from the url."""
        return session.get(url_, headers={'Range': f'bytes={range_}'}).content

    # Resolve user directory shortcuts and relative paths
    output_dir = Path(output_dir).expanduser().resolve()

    # If the path exists, make sure it is a directory
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError('output_dir must be a path to a directory')

    # Create a session
    session = get_session(**session_kwargs)

    # HEAD the endpoint and follow redirects to get the actual download URL and Content-Length
    r = session.head(url, allow_redirects=True)
    r.raise_for_status()
    content_length = int(r.headers['Content-Length'])
    download_url = r.url

    # Get the full file path
    output_file_name = urllib.parse.urlsplit(download_url).path.rsplit('/', 1)[1]
    output_path = output_dir / output_file_name

    # Check for existing output file
    open_mode = 'wb'
    start = 0
    if output_path.exists():
        # Since we check the allowed values of if_exists above, we can be sure that it is either
        #  skip, resume, or overwrite. If it is overwrite, we treat it as if the file did not exist.
        if if_exists == 'skip':
            return output_path
        if if_exists == 'resume':
            start = output_path.stat().st_size
            open_mode = 'ab'
            # Don't attempt the download if the existing file is the same size as the download
            if start == content_length:
                return output_path

    # Create the parent directory, if it does not exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # If we can use range requests, make concurrent requests to the byte ranges we need...
    with ThreadPoolExecutor(max_workers=20) as executor:
        with output_path.open(mode=open_mode) as dst:
            with tqdm(total=round(content_length / 1000000., 1), unit='M') as pbar:
                pbar.update(round(start / 1000000., 1))
                for chunk in executor.map(
                        partial(_fetch_range, download_url),
                        _get_ranges(content_length, chunk_size, start=start)
                ):
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

    try:
        return session.get(f'collections/{collection_id}/items/{item_id}').json()
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(f'Collection "{collection_id}" and/or item {item_id} do not exist.')
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})')


def get_archive_info(archive_id: str, **session_kwargs) -> dict:
    """Gets info for the given archive from the ``/archive/{archive_id}/info`` endpoint as a
    JSON-like dictionary.

    The JSON object returned by the API has the following properties:

    - ``collection``: The ID of the Collection that this archive is associated with.
    - ``dataset``: The ID of the dataset that this archive's Collection belongs to.
    - ``size``: The size of the archive (in bytes)
    - ``types``: The types associated with this archive's Collection. Will be one of
      ``"source_imagery"`` or ``"label"``.

    Parameters
    ----------
    archive_id : str
        The ID of the archive. This is the same as the Collection ID.
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    archive_info : dict
        JSON-like dictionary representing the API response.
    """
    session = get_session(**session_kwargs)
    try:
        return session.get(f'archive/{archive_id}/info').json()

    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(f'Archive "{archive_id}" does not exist.') from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})') from None


def download_archive(
        archive_id: str,
        output_dir: Path = None,
        *,
        if_exists: str = 'resume',
        **session_kwargs
) -> Path:
    """Downloads the archive with the given ID to an output location (current working directory by default).

    The ``if_exists`` argument determines how to handle an existing archive file in the output directory. The default
    behavior (defined by ``if_exists="resume"``) is to resume the download by requesting a byte range starting at the
    size of the existing file. If the existing file is the same size as the file to be downloaded (as determined by the
    ``Content-Length`` header), then the download is skipped. You can automatically skip download using ``if_exists="skip"``
    (this may be faster if you know the download was not interrupted, since no network request is made to get the archive
    size). You can also overwrite the existing file using ``if_exists="overwrite"``.

    Parameters
    ----------
    archive_id : str
        The ID of the archive to download. This is the same as the Collection ID.
    output_dir : Path
        Path to which the archive will be downloaded. Defaults to the current working directory.
    if_exists : str, optional
        How to handle an existing archive at the same location. If ``"skip"``, the download will be skipped. If ``"overwrite"``,
        the existing file will be overwritten and the entire file will be re-downloaded. If ``"resume"`` (the default), the
        existing file size will be compared to the size of the download (using the ``Content-Length`` header). If the existing
        file is smaller, then only the remaining portion will be downloaded. Otherwise, the download will be skipped.
    **session_kwargs
        Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

    Returns
    -------
    output_path : Path
        The full path to the downloaded archive file.

    Raises
    ------
    ValueError
        If ``if_exists`` is not one of ``"skip"``, ``"overwrite"``, or ``"resume"``.
    """
    output_dir = output_dir if output_dir is not None else Path.cwd()

    try:
        return _download(
            f'archive/{archive_id}',
            output_dir=output_dir,
            if_exists=if_exists,
            **session_kwargs
        )
    except HTTPError as e:
        if e.response.status_code == 404:
            raise EntityDoesNotExist(
                f'Archive "{archive_id}" does not exist and may still be generating. Please try again later.') from None
        raise MLHubException(f'An unknown error occurred: {e.response.status_code} ({e.response.reason})')
