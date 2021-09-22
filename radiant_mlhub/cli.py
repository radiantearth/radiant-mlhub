import configparser
import os
from pathlib import Path

import click

from .__version__ import __version__
from .session import Session


@click.group()
@click.version_option(version=__version__)  # type: ignore[misc]
def mlhub() -> None:
    """CLI tool for the radiant_mlhub Python client."""


@mlhub.command()
@click.option('--profile', default='default', help='The name of the profile to configure.')  # type: ignore[misc]
@click.option('--api-key', prompt='API Key', help='The API key to use for this profile.')  # type: ignore[misc]
def configure(profile: str, api_key: str) -> None:
    """Interactively set up radiant_mlhub configuration file.

    This tool walks you through setting up a ~/.mlhub/profiles file and adding an API key. If you do not
    provide a --profile option, it will update the "default" profile. If you do not provide an --api-key
    option, you will be prompted to enter an API key by the tool.

    If you need to change the location of the profiles file, set the MLHUB_HOME environment variable before
    running this command.

    For details on profiles and authentication for the radiant_mlhub client, please see the official
    Authentication documentation:

    https://radiant-mlhub.readthedocs.io
    """

    mlhub_home = Path(os.getenv(Session.MLHUB_HOME_ENV_VARIABLE, Path.home() / '.mlhub'))
    config_path = mlhub_home / 'profiles'

    config = configparser.ConfigParser()
    config.read(config_path)

    existing_api_key = config.get(profile, 'api_key', fallback=None)

    if existing_api_key and not click.confirm(f'Overwrite existing API Key (****{existing_api_key[-6:]})'):
        raise click.Abort

    if not config.has_section(profile):
        config[profile] = {}
    config[profile]['api_key'] = api_key

    # Create the parent directory if it does not exist
    config_path.parent.mkdir(exist_ok=True)

    with config_path.open('w') as dst:
        config.write(dst)

    print(f'Wrote profile to {config_path}')
