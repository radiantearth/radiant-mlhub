import os
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Iterator, Optional, Union

from .session import get_session

try:
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    # Handles this issue: https://github.com/tqdm/tqdm/issues/1082
    from tqdm import tqdm


def _download(
        url: str,
        output_dir: Union[str, Path],
        *,
        if_exists: str = 'resume',
        chunk_size: int = 5000000,
        api_key: Optional[str] = None, profile: Optional[str] = None
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
    output_dir = os.fspath(output_dir)
    if if_exists not in {'skip', 'overwrite', 'resume'}:
        raise ValueError('if_exists must be one of "skip", "overwrite", or "resume"')

    def _get_ranges(total_size: int, interval: int, start: int = 0) -> Iterator[str]:
        """Internal function for getting byte ranges from a total size and interval/chunk size."""
        while True:
            end = min(start + interval - 1, total_size)
            yield f'{start}-{end}'
            start += interval
            if start >= total_size:
                break

    def _fetch_range(url_: str, range_: str) -> bytes:
        """Internal function for fetching a byte range from the url."""
        return session.get(url_, headers={'Range': f'bytes={range_}'}).content

    # Resolve user directory shortcuts and relative paths
    output_dir = Path(output_dir).expanduser().resolve()

    # If the path exists, make sure it is a directory
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError('output_dir must be a path to a directory')

    # Create a session
    session = get_session(api_key=api_key, profile=profile)

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
