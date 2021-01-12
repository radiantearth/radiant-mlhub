import click

from .__version__ import __version__


@click.group(name='mlhub')
@click.version_option(version=__version__)
def main():
    """CLI tool for the radiant_mlhub Python client."""
