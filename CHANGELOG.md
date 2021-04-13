# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## \[Unreleased\]

### Fixed

* Allow user-defined `profiles` location (#27)

### Added

* Available as `conda` package via `conda-forge` (#34)

    ```console
    $ conda install -c conda-forge radiant-mlhub
    ```

## \[v0.1.2\]

### Fixed

* Implicit dependency on `typing_extensions` (#29)

### Developer

* Manually caches properties instead of using `functools.cached_property`/`backports.cached_property`

## \[v0.1.1\]

### Added

* Ability to resume archive downloads(#24)
* Automatically retry requests that fail due to connection issues (#24)

## \[v0.1.0\]

First working `alpha` release of the Radiant MLHub Python client. 

Includes support for:

* Configuring authentication using profiles or environment variables
* Listing datasets and collections
* Fetching datasets and collections by ID
* Downloading collection archives
