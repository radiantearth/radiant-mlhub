import configparser
from pathlib import Path
from typing import TYPE_CHECKING

from radiant_mlhub.cli import mlhub

if TYPE_CHECKING:
    from click.testing import CliRunner as CliRunner_Type


class TestCLI:

    def test_version(self, cli_runner: "CliRunner_Type") -> None:
        result = cli_runner.invoke(mlhub, ['--version'])
        assert result.output.rstrip('\n') == 'mlhub, version 0.3.0'

    def test_configure(self, isolated_cli_runner: "CliRunner_Type") -> None:
        new_home = Path.cwd()

        # Monkeypatch the user's home directory to be the temp directory (CWD)
        env = {
            'HOME': str(new_home),
            'USERPROFILE': str(new_home)
        }

        result = isolated_cli_runner.invoke(mlhub, ['configure'], input='testapikey\n', env=env)
        assert result.exit_code == 0, result.output

        # Should create a profiles file in the "HOME" directory
        profile_path = new_home / '.mlhub' / 'profiles'
        assert profile_path.exists()

        config = configparser.ConfigParser()
        config.read(profile_path)

        assert config.get('default', 'api_key') == 'testapikey'

        # Should abort if an api key exists and user does not confirm overwrite
        result = isolated_cli_runner.invoke(mlhub, ['configure'], input='testapikey\nn\n', env=env)
        assert result.exit_code == 1, result.output

    def test_configure_user_defined_home(self, isolated_cli_runner: "CliRunner_Type") -> None:
        new_home = Path.cwd()

        mlhub_home = new_home / 'some-directory' / '.mlhub'
        mlhub_home.mkdir(parents=True)

        result = isolated_cli_runner.invoke(
            mlhub,
            ['configure'],
            input='userdefinedhome\n',
            env={'MLHUB_HOME': str(mlhub_home)}
        )
        assert result.exit_code == 0, result.output

        # Should create a profiles file in the "HOME" directory
        profile_path = mlhub_home / 'profiles'
        assert profile_path.exists()

        config = configparser.ConfigParser()
        config.read(profile_path)

        assert config.get('default', 'api_key') == 'userdefinedhome'
