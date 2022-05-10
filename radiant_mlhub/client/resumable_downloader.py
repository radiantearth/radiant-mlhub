import http
from logging import getLogger
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3 import Retry

from ..if_exists import DownloadIfExistsOpts
from ..session import Session as MLHubSession

http.client.HTTPConnection.debuglevel = 0  # change to > 0 for verbose logging


log = getLogger(__name__)

CHUNK_SIZE = 1024
CHUNK_UNIT = 'KB'

# TODO: it should not be necessary to send x-ms-version: AZ_STORAGE_VERSION
# just to get http range request support. could be fixed by configuring
# the blob storage container?
# Azure blob storage: older storage versions don't support desired range requests
# * https://docs.microsoft.com/en-us/rest/api/storageservices/Specifying-the-Range-Header-for-Blob-Service-Operations
# * https://docs.microsoft.com/en-us/rest/api/storageservices/versioning-for-the-azure-storage-services
#
AZ_STORAGE_VERSION = '2021-06-08'


class ResumableDownloader():
    """
    Resumable downloader, for a single file.

    * Similar to _download_collection_archive_chunked(), but this is not parallelized.
    * Supports DownloadIfExistsOpts.
    * Displays progress bar.
    * Has backoff/retry logic (if requests session is not overridden)
    """
    session: requests.Session
    url: str
    out_file: Path
    if_exists: DownloadIfExistsOpts
    disable_progress_bar: bool
    chunk_size: int
    chunk_unit: str
    desc: Optional[str]

    def __init__(
            self,
            url: str,
            out_file: Path,
            desc: Optional[str] = None,
            session: Optional[requests.Session] = None,
            if_exists: DownloadIfExistsOpts = DownloadIfExistsOpts.overwrite,
            disable_progress_bar: bool = True,
            chunk_size: int = CHUNK_SIZE,
            chunk_unit: str = CHUNK_UNIT
            ):
        self.url = url
        self.out_file = out_file
        self.if_exists = if_exists
        self.disable_progress_bar = disable_progress_bar
        self.chunk_size = chunk_size
        self.chunk_unit = chunk_unit
        self.desc = desc

        if session:
            self.session = session
        else:
            # no session provided, configure own session using backoff/retry logic
            retry_strategy = Retry(
                total=5,
                backoff_factor=0.2,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            s = requests.Session()
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            self.session = s

    def run(self) -> None:
        self.out_file.parent.mkdir(exist_ok=True, parents=True)
        if self.out_file.exists():
            if self.if_exists == DownloadIfExistsOpts.skip:
                log.debug(f'{self.out_file.resolve()} -> skip')
                return
            elif self.if_exists == DownloadIfExistsOpts.overwrite:
                self.out_file.unlink()
                log.debug(f'{self.out_file.resolve()} -> overwrite')
            elif self.if_exists == DownloadIfExistsOpts.resume:
                # make HEAD request to get content-length (detect whether to resume)
                resp = self.session.head(self.url, allow_redirects=True)
                resp.raise_for_status()
                content_len = int(resp.headers['content-length'])
                size = self.out_file.stat().st_size
                assert size <= content_len, 'unexpected asset size on filesystem'
                if size == content_len:
                    return  # nothing to resume
                log.debug(f'{self.out_file.resolve()} -> resume')

        with open(self.out_file, mode='ab') as fh:
            if isinstance(self.session, MLHubSession) or 'blob.core.windows.net' in self.url:
                req_headers = {'x-ms-version': AZ_STORAGE_VERSION}
            else:
                req_headers = dict()
            pos = fh.tell()
            if pos > 0:
                req_headers['range'] = f'bytes={pos}-'
            resp = self.session.get(self.url, headers=req_headers, stream=True)
            resp.raise_for_status()
            if resp.ok:
                assert 'bytes' in resp.headers.get('accept-ranges', ''), \
                    'HTTP Range request not supported'
                if 'range' in req_headers:
                    assert resp.status_code == 206, \
                        "Unexpected http status code: check blob storage version's support for range header."
            if pos > 0:
                content_range = resp.headers['content-range']
                content_len = int(content_range.split('/')[1])
            else:
                content_len = int(resp.headers['content-length'])

            if pos >= content_len:
                return  # no content left to resume

            for data in tqdm(
                iterable=resp.iter_content(chunk_size=self.chunk_size),
                total=(content_len - pos) // self.chunk_size,
                initial=pos // self.chunk_size,
                unit=self.chunk_unit,
                desc=self.desc if self.desc else f'fetch {self.url}',
                disable=self.disable_progress_bar,
            ):
                fh.write(data)
