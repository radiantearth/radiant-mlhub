from pathlib import Path
import configparser

from radiant_mlhub.cli import mlhub


class TestCLI:

    def test_version(self, cli_runner):
        result = cli_runner.invoke(mlhub, ['--version'])
        assert result.output.rstrip('\n') == 'mlhub, version 0.1.1'

    def test_configure(self, isolated_cli_runner, monkeypatch):
        new_home = Path.cwd()

        # Monkeypatch the user's home directory to be the temp directory (CWD)
        monkeypatch.setenv('HOME', str(new_home))  # Linux/Unix
        monkeypatch.setenv('USERPROFILE', str(new_home))  # Windows

        result = isolated_cli_runner.invoke(mlhub, ['configure'], input='testapikey\n')
        assert result.exit_code == 0, result.output

        # Should create a profiles file in the "HOME" directory
        profile_path = new_home / '.mlhub' / 'profiles'
        assert profile_path.exists()

        config = configparser.ConfigParser()
        config.read(profile_path)

        assert config.get('default', 'api_key') == 'testapikey'

        # Should abort if an api key exists and user does not confirm overwrite
        result = isolated_cli_runner.invoke(mlhub, ['configure'], input='testapikey\nn\n')
        assert result.exit_code == 1, result.output
