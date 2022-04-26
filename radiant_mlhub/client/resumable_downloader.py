import base64
import binascii
import hashlib
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

# TODO: make md5 checksum validation gracefully fallback if there is no content-md5 header (e.g. S3 assets, like the spacenet* datasets)

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
    md5_check: bool
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
            md5_check: bool = True,
            chunk_size: int = CHUNK_SIZE,
            chunk_unit: str = CHUNK_UNIT
            ):
        self.url = url
        self.out_file = out_file
        self.if_exists = if_exists
        self.disable_progress_bar = disable_progress_bar
        self.md5_check = md5_check
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

    def validate(self) -> bool:
        if not self.md5_check:
            return False
        if not self.out_file.exists():
            return False
        checksum_file = Path(f'{self.out_file}.md5')
        if not checksum_file.exists():
            return False

        # read expected checksum (md5, hex encoded)
        with open(checksum_file) as fh:
            expect_checksum = fh.read()

        # calculate actual checksum
        actual_bytes = self.out_file.read_bytes()
        h = hashlib.md5(actual_bytes)
        got_checksum = h.digest().hex()

        if got_checksum == expect_checksum:
            return True
        return False

    def run(self) -> None:
        self.out_file.parent.mkdir(exist_ok=True, parents=True)
        if self.out_file.exists():
            if self.if_exists == DownloadIfExistsOpts.overwrite:
                self.out_file.unlink()
                log.info(f'{self.out_file.resolve()} -> overwrite')
            else:
                # not overwriting
                if self.validate():
                    log.debug(f'{self.out_file.resolve()} -> exists, is valid')
                    return  # early out
                else:
                    # exists, not overwriting, invalid file
                    if self.if_exists == DownloadIfExistsOpts.resume:
                        log.debug(f'{self.out_file.resolve()} -> resume')
                    elif self.if_exists == DownloadIfExistsOpts.skip:
                        raise RuntimeError(f'{self.out_file.name} exists but is invalid -> cannot skip')

        with open(self.out_file, mode='ab') as f:
            if isinstance(self.session, MLHubSession) or 'blob.core.windows.net' in self.url:
                req_headers = {'x-ms-version': AZ_STORAGE_VERSION}
            else:
                req_headers = dict()
            pos = f.tell()
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

            checksum = resp.headers.get('content-md5', None)
            if checksum:
                try:
                    # convert checksum from base64 to hex (for convenience)
                    checksum_hex = base64.b64decode(checksum, validate=True).hex()
                    with open(f'{self.out_file}.md5', mode='w') as fh:
                        fh.write(checksum_hex)
                except binascii.Error as e:
                    # this would only happen if the md5sum was not base64 encoded
                    log.error(e)
                    raise e

            if pos >= content_len:
                if self.md5_check:
                    if self.validate():
                        return
                    else:
                        raise IOError(f'Failed to validate md5 checksum for {self.out_file}')
                return

            for data in tqdm(
                iterable=resp.iter_content(chunk_size=self.chunk_size),
                total=(content_len - pos) // self.chunk_size,
                initial=pos // self.chunk_size,
                unit=self.chunk_unit,
                desc=self.desc if self.desc else f'fetch {self.url}',
                disable=self.disable_progress_bar,
            ):
                f.write(data)
            f.flush()

        if self.md5_check and not self.validate():
            raise IOError(f'File {self.url} failed validation after download.')
