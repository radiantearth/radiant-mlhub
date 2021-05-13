# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.0]

### Changed

* Pins PySTAC to v0.5.4 ([#43](https://github.com/radiantearth/radiant-mlhub/pull/43))

   Later versions automatically resolve links, which was leading to unnecessary network requests and
   issues with matching in VCR.py

### Fixed

* Allow user-defined `profiles` location ([#27](https://github.com/radiantearth/radiant-mlhub/issues/27))
* License file is now included in the distribution ([#37](https://github.com/radiantearth/radiant-mlhub/issues/37))

### Added

* Properties to get archive sizes without downloading (`Collection.archive_size` and
  `Dataset.total_archive_size`) ([#44](https://github.com/radiantearth/radiant-mlhub/pull/40))
* New attributes on `Dataset` class (`doi`, `citation`, and `registry_url`) ([#40](https://github.com/radiantearth/radiant-mlhub/pull/40))
* `Collection.registry_url` property to get the URL for the Collection's registry page ([#39](https://github.com/radiantearth/radiant-mlhub/pull/39))
* Available as `conda` package via `conda-forge` ([#34](https://github.com/radiantearth/radiant-mlhub/issues/29))

    ```console
    $ conda install -c conda-forge radiant-mlhub
    ```

### Developer

* Switch to using [pytest-recording](https://pypi.org/project/pytest-recording/) ([VCR.py] under the
  hood) for mocking API responses ([#43](https://github.com/radiantearth/radiant-mlhub/pull/43))

## [v0.1.3]

### Fixed

* New attributes in the `/dataset` response will no longer break the `Dataset` class
  ([#42](https://github.com/radiantearth/radiant-mlhub/pull/42))

## [v0.1.2]

### Fixed

* Implicit dependency on `typing_extensions` ([#29](https://github.com/radiantearth/radiant-mlhub/issues/29))

### Developer

* Manually caches properties instead of using `functools.cached_property`/`backports.cached_property`

## [v0.1.1]

### Added

* Ability to resume archive downloads([#24](https://github.com/radiantearth/radiant-mlhub/issues/24))
* Automatically retry requests that fail due to connection issues ([#24](https://github.com/radiantearth/radiant-mlhub/issues/24))

## [v0.1.0]

First working `alpha` release of the Radiant MLHub Python client. 

Includes support for:

* Configuring authentication using profiles or environment variables
* Listing datasets and collections
* Fetching datasets and collections by ID
* Downloading collection archives

[v0.2.0]: https://github.com/radiantearth/radiant-mlhub/releases/tag/v0.2.0
[v0.1.3]: https://github.com/radiantearth/radiant-mlhub/releases/tag/v0.1.3
[v0.1.2]: https://github.com/radiantearth/radiant-mlhub/releases/tag/v0.1.2
[v0.1.1]: https://github.com/radiantearth/radiant-mlhub/releases/tag/v0.1.1
[v0.1.0]: https://github.com/radiantearth/radiant-mlhub/releases/tag/v0.1.0
[VCR.py]: https://vcrpy.readthedocs.io/en/latest/usage.html
