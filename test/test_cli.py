from radiant_mlhub.cli import main


class TestCLI:

    def test_version(self, cli_runner):
        result = cli_runner.invoke(main, ['--version'])
        assert result.output.rstrip('\n') == 'mlhub, version 0.0.2'
