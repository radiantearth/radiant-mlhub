# Contributing

## Development Environment

Install development dependencies:

```shell
> pip install -r requirements_dev.txt
```

## Branches
The `main` branch represents the latest stable version of the `radiant-mlhub` Python client. The `dev` branch 
is where active feature development takes place. When developing new features, please create a branch off of the 
`dev` branch (ideally with a `feature-` prefix) and create a PR for that branch against`dev` 
when it is ready for review. 

To work on a hotfix for bugs affecting the "production" code (code that is part of a released package), please create 
a branch off of `main` (ideally with a `hotfix-` prefix) and create a PR for that branch against `main` 
when it is ready for review.

## Tests

This library uses [`pytest`](https://docs.pytest.org/en/stable/) for unit testing, [`flake8`](https://flake8.pycqa.org/en/latest/) 
for code style checking, and [`mypy`](https://mypy.readthedocs.io/en/stable/) for type checking. We use [`tox`](https://tox.readthedocs.io/en/latest/examples.html)
run each of these tools against all supported Python versions.

To run against all supported Python versions in parallel:

```shell
> tox -p
```

To run against just Python 3.8:

```shell
> tox -e py38
```

*Note that you must have all supported Python versions installed in order to run tests against them. See [`tox-pyenv`](https://pypi.org/project/tox-pyenv/) if you are 
using `pyenv` to manage your installed Python versions.*  

## Releases

When the code on the `dev` branch has stabilized, we will cut a new release using the following procedure:

1) Create a `release-<version>` branch from `dev`, where `<version>` is the version to be released

2) [Run `tbump`](https://github.com/TankerHQ/tbump#usage) to bump the package to the desired 
   version **using the `--only-patch` option to ensure you don't create and push the tag yet**.

3) Test and make any last-minute changes

4) Put in a PR against `main`

   This will trigger the CI to run unit tests and to publish a test package to TestPyPi.

5) Approve and merge into `main`

   Once the PR has been approved, merge into `main`

6) Tag and publish release

   This will trigger the CI to publish the package to PyPi

7) Merge release branch into `dev`

  This ensures that `dev` stays up-to-date with any changes made during the release process (including updating 
  the package version). There is no need to put in a PR against `dev`, since the changes have already been 
  approved for `main`.