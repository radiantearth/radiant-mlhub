import os
from urllib3 import Retry
from typing import Optional


def config() -> Optional[Retry]:
    """
    Common configuration for http backoff/retry strategy.

    `{backoff factor} * (2 ** ({number of total retries} - 1))`

    `0.2 * (2 ** (10 - 1)) = 102.4 seconds`
    """
    if 'PYTEST_CURRENT_TEST' in os.environ and 'MLHUB_CI' in os.environ:
        return None

    return Retry(
        backoff_factor=0.2,
        status_forcelist=[
            404, 408, 409, 413, 423, 429,
            500, 502, 503, 504
        ]
    )
