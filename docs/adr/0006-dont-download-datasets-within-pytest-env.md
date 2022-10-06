# 6. Don't download datasets within pytest environment

Date: 2022-09-20

## Status

Accepted

## Context

Our test setup uses VCR.py, which does not support multithreaded usage of the
`requests` library. Our dataset downloader does use multithreading in it's
`requests` invocation. Therefore some short-circuit code was added in the
downloader, to rely on mocking and fixtures for file downloads, and to not
actually perform downloads at the http level. This worked for our unit testing
needs, but broke the downloader for other users of `pytest`. In issue
[#148](https://github.com/radiantearth/radiant-mlhub/issues/148) it was
observed that the dataset downloader was not working inside user's `pytest`
tests.

## Decision

No solution is forthcoming for VCR.py to support multithreading of the
`requests` library, so the short circuit code in the downloader still seems
necessary.

The addition of a new environment variable `MLHUB_CI=true` is just a flag
affirming that the above workaround is in-force, in addition to checking if we
are running in a `pytest` test. This environment variable is set in the
Continuous Integration (CI) in GitHub Actions. This environment variable also
needs to be set by the developer who is running pytest locally while developing
on radiant-mlhub.

## Consequences

We can continue to use VCR.py in our unit tests, and also users can use the
MLHub downloader in their own `pytest` tests if they desire.
