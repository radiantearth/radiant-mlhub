# Contributing

Contributions to this project are welcome and encouraged! Please be sure to
review our [Code of Conduct](./CODE_OF_CONDUCT.md) before participating in any
community discussions in this repo.

## Issues

The easiest way to contribute to the `radiant-mlhub` library is by opening
issues to report bugs or request features that might be useful to you or
others. Before opening a new issue, please review the
[documentation](https://radiant-mlhub.readthedocs.io/) and existing
[issues](https://github.com/radiantearth/radiant-mlhub/issues) (both open and
closed) to see if the topic is already covered by an existing issue. Issues in
this repository should pertain directly to the `radiant_mlhub` Python client
itself and not the [Radiant MLHub API](https://mlhub.earth/) or the datasets
contained therein. For questions and issues regarding those resources, please
email [support@radiant.earth](mailto:support@radiant.earth). If it is unclear
whether the issue pertains to the API or the Python client, please start by
emailing [support@radiant.earth](mailto:support@radiant.earth) and we will help
to assess the scope of the issue.

Issues in this repository follow one of 2 templates: bug reports or feature
requests. For more general questions or troubleshooting that does not fall into
one of these two categories, please email us at
[support@radiant.earth](mailto:support@radiant.earth). When creating a new
issue, please follow the appropriate template as closely as possible and
provide as much detail as you can.

## Pull Requests

We welcome and encourage pull requests from the community to address bugs or
feature requests. Before submitting a pull request, please open an issue to
discuss the feature or bug fix that you intend to implement. This will help us,
and the rest of our user community, give input on the design for any changes
and ensure that we are not already doing work on similar features.

All branches should originate from the `main` branch and all PRs should be made
against the `main` branch.

New PRs will use our [PR template](https://github.com/radiantearth/radiant-mlhub/blob/main/.github/pull_request_template.md), which you should follow and fill in.

## Architecture Decision Records (ADR)

This library uses Architecture Decision Records (ADR). See [docs/adr](./docs/adr/0001-record-architecture-decisions.md).

## Development Environment

Install development dependencies:

```bash
pip install -r requirements_dev.txt
pip install -r requirements_docs.txt
pip install -r requirements_testing.txt
```

## Linter

This library uses [flake8](https://flake8.pycqa.org/) for Python
linting. Run the `flake8` command to see linting errors. `flake8` is also
run by the Continuous Integration (CI) setup in GitHub Actions.

## Type Checker

This library uses Python type hinting, and
[mypy](https://mypy.readthedocs.io/) for type checking. Run the `mypy
radiant_mlhub/` command to see type checking errors. `mypy` is also run by the
Continuous Integration (CI) setup in GitHub Actions.

## Unit Tests

For unit testing, this library uses [pytest](https://docs.pytest.org/),
[VCR.py](https://vcrpy.readthedocs.io/) and
[pytest-recording](https://github.com/kiwicom/pytest-recording). There is some
initial setup for running tests locally:

1. Create an API key on the staging server at [https://staging.mlhub.earth/](https://staging.mlhub.earth/).
2. Set the `MLHUB_API_KEY` environment variable to your own API key from staging:

   ```bash
   export MLHUB_API_KEY=***********
   ```

3. Set the `MLHUB_CI` environment variable. The purpose of the MLHUB_CI
   environment variable is documented in [ADR #6](/docs/adr/0006-dont-download-datasets-within-pytest-env.md).

   ```bash
   export MLHUB_CI=true
   ```

4. Finally, run `pytest` command.

### VCR.py Cassettes

Your API key will be used to make new requests, but will *not* be recorded in
any of the cassettes. All user-specific download links are also sanitized
before being recorded to a cassette.

The default record mode is `--record-mode=once` which means when you run
`pytest` any new tests which are marked as VCR.py tests will automatically get
recorded as new cassettes. New cassettes should be then be committed in Git.

To re-record a cassette use:

```bash
pytest {path_to_test(s)} --record-mode=rewrite
```

To re-record all cassettes (note, this is also done periodically in a scheduled
job in CI).

```bash
pytest --record-mode=rewrite
```

To emulate what the CI runner normally does in it's workflow for PRs and merges:

```bash
pytest --record-mode=once --block-network
```

## Releases

*NOTE: This section is primarily for the maintainers and will almost never be
necessary for community contributions.*

### Preparation

* Confirm the `setup.py` and `requirements_*.txt` files are all up to date with
correct dependencies.

* Run pytest in `pytest --record-mode=rewrite` in your local development
environment. It is not necessary to commit the new cassettes, however, this
should step reveal if there were any regressions between the VCR.py saved state
and our staging API.

## Release Steps

When the code on the `main` branch has stabilized, make a new release
using the following steps:

1) Create a `release/<version>` branch from `main`, where `<version>` is the
version to be released (e.g. `v1.42.99`). This library uses [Semantic
Versioning](https://semver.org/).

2) [Run `tbump`](https://github.com/TankerHQ/tbump) to bump the package
to the desired version:

   ```shell
   tbump --no-push --no-tag <NEW_VERSION>
   # example (notice: omit the `v`!)
   tbump --no-push --no-tag 1.42.99
   ```

3) Commit changes to the CHANGELOG.md including the new version, and not
forgetting the comparison links at the bottom.

4) Test and make any final changes on the `release/*` branch, e.g.
`release/v1.42.99`.

5) Put in a PR against `main`. This will trigger the CI to run unit tests and
to publish a test package to [TestPyPi](https://test.pypi.org/). Preview the
release there, making any changes as needed in the PR.

6) Once the PR has been approved, merge into `main`.

7) Create a [Git Tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging) at the
head of main branch. It is recommended to use an *annotated* git tag, which
must be done via the Git command line client, not the GitHub UI.

   ```bash
   # example using v1.42.99
   git tag -a v1.42.99 -m "radiant-mlhub Python client release v1.42.99"
   git push origin --tags
   # or
   git push origin v1.42.99
   ```

8) Publish a release in the GitHub UI. Name the release the same as the tag,
e.g. `v1.42.99`. This will trigger the CI to publish the package to PyPi.

9) After the release has been published to PyPi, you should also update the
recipe in the [`conda-forge` feedstock](https://github.com/conda-forge/radiant-mlhub-feedstock)
to use the new release. See the README in that repo for instructions on how to
update the recipe. There are some gotchas with the Conda Forge publishing. Some
points to remember:

   * There is a fork of the feedstock in the [radiantearth GitHub org](https://github.com/radiantearth/radiant-mlhub-feedstock), which should
   be kept up to date with the upstream repo, for archival purposes. However
   for publishing releases, it's strongly recommended to use a personal fork of
   the feedstock repo. `conda-smithy` can be used via the GitHub CI runner, but
   this works only with personal forks, not in organizational forks, because of
   GitHub permissions issues, according to Conda Forge docs.

   * In the feedstock recipe, there is a [SHA256
   checksum](https://github.com/conda-forge/radiant-mlhub-feedstock/blob/main/recipe/meta.yaml#L8-L10),
   which must be copied from PyPi after the package has been published: To
   see it, browse to: [https://pypi.org/project/radiant-mlhub/](https://pypi.org/project/radiant-mlhub/) | Download
   Files | Source Distribution | view hashes

   * The [feedstock](https://github.com/conda-forge/radiant-mlhub-feedstoc)
   recipe has it's own copy of the package dependencies for the conda package,
   in `recipe/meta.yaml`. (Yet another place where the radiant-mlhub Python
   dependencies have to be updated, and kept up to date).

   * Conda Forge may take several hours to update file assets upon release
   (unknown why it's so much slower than PyPi).

10) Test out the new published release by installing it using both `pip` and
`conda`.

11) Update any and all external MLHub documentation, notebooks, or example code
which is pointing to older releases. Ideally semantic versioning can be used to
lessen the burden of updating example code or requirements files.
