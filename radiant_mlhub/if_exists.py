from enum import Enum


class DownloadIfExistsOpts(str, Enum):
    """Allowed values for `download`'s `if_exists` option."""
    resume = "resume"
    skip = "skip"
    overwrite = "overwrite"
