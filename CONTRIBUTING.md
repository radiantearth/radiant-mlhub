# Contributing

Contributions to this project are welcome and encouraged! Please be sure to review our 
[Code of Conduct](./CODE_OF_CONDUCT.md) before participating in any community discussions in this repo.

## Issues

The easiest way to contribute to the `radiant-mlhub` library is by opening issues to report bugs or request features 
that might be useful to you or others. Before opening a new issue, please review the 
[documentation](https://radiant-mlhub.readthedocs.io/en/latest/) and existing 
[issues](https://github.com/radiantearth/radiant-mlhub/issues) (both open and closed) to see if the topic is already 
covered by an existing issue. Issues in this repository should pertain directly to the `radiant_mlhub` Python client 
itself and not the [Radiant MLHub API](https://mlhub.earth/) or the datasets contained therein. For questions and 
issues regarding those resources, please email [support@radiant.earth](mailto:support@radiant.earth). If it is unclear 
whether the issue pertains to the API or the Python client, please start by emailing 
[support@radiant.earth](mailto:support@radiant.earth) and we will help to assess the scope of the issue.

Issues in this repository follow one of 2 templates: bug reports or feature requests. For more general questions or 
troubleshooting that does not fall into one of these two categories, please email us at 
[support@radiant.earth](mailto:support@radiant.earth). When creating a new issue, please follow the appropriate template 
as closely as possible and provide as much detail as you can. 

## Pull Requests

We welcome and encourage pull requests from the community to address bugs or feature requests. Before submitting a pull
request, please open an issue to discuss the feature or bug fix that you intend to implement. This will help us, and the 
rest of our user community, give input on the design for any changes and ensure that we are not already doing work on 
similar features.

All branches should originate from the `main` branch and all PRs should be made against the `main` branch.

New PRs will use our PR template, which includes the following checklist:

* Unit tests have been added/updated to cover changes
* Documentation has been added/updated
* An entry has been added to the [CHANGELOG](./CHANGELOG.md) (if necessary)

## Development

## Development Environment

Install development dependencies:

```shell
> pip install -r requirements_dev.txt
```

## Tests

This library uses [`pytest`](https://docs.pytest.org/en/stable/) for unit testing, 
[`flake8`](https://flake8.pycqa.org/en/latest/) and [`flake8-nb`](https://pypi.org/project/flake8-nb/)
for code style checking, and [`mypy`](https://mypy.readthedocs.io/en/stable/) for type checking.
We also use [`tox`](https://tox.readthedocs.io/en/latest/examples.html) run each of these tools against
all supported Python versions.

To run against all supported Python versions in parallel:

```shell
> tox -p
```

To run against just Python 3.8, for example:

```shell
> tox -e py38
```

*Note that you must have all supported Python versions installed in order to run tests against them. See 
[`tox-pyenv`](https://pypi.org/project/tox-pyenv/) if you are using `pyenv` to manage your installed Python versions.*  

### VCR.py Cassettes

If you need to re-record any of the VCR.py cassettes, you will need to create a `test/.env` file
with the following content:

```
MLHUB_API_KEY=<SUBSTITUTE_VALID_API_KEY_HERE>
```

The API key will be used to make new requests, but will *not* be recorded in any of the cassettes.
All user-specific download links are also sanitized before being recorded to a cassette. 

To re-record a cassette use:

```
pytest {path_to_test(s)} --record-mode rewrite --block-network
```

## Releases

*NOTE: This section is primarily for the maintainers and will almost never be necessary for community contributions.*

When the code on the `main` branch has stabilized, we will cut a new release using the following procedure:

1) Create a `release/<version>` branch from `main`, where `<version>` is the version to be released
   (e.g. `v1.0.0`).

2) [Run `tbump`](https://github.com/TankerHQ/tbump#usage) to bump the package to the desired 
   version:

   ```shell
   tbump --no-push --no-tag <NEW_VERSION>
   ```

3) Commit changes to the CHANGELOG.md including the new version, and the compare
   links at the bottom.

4) Test and make any final changes on the `release/*` branch

5) Put in a PR against `main`

   This will trigger the CI to run unit tests and to publish a test package to TestPyPi.

6) Approve and merge into `main`

   Once the PR has been approved, merge into `main`

7) Tag and publish release. Use an annotated git tag.

   This will trigger the CI to publish the package to PyPi
  
After the release has been published to PyPi, you should also update the recipe in the [`conda-forge` 
feedstock](https://github.com/conda-forge/radiant-mlhub-feedstock) to use the new release. See the README in that repo 
for instructions on how to update the recipe. 