import configparser
import os.path
import urllib.parse

import pytest
from requests_mock.exceptions import NoMockAddress

from radiant_mlhub.exceptions import APIKeyNotFound, AuthenticationError
from radiant_mlhub.session import Session, get_session


class TestResolveAPIKeys:

    @pytest.fixture(scope='function')
    def mock_profile(self, monkeypatch, tmp_path):
        config = configparser.ConfigParser()

        config['default'] = {'api_key': 'defaultapikey'}
        config['other-profile'] = {'api_key': 'otherapikey'}
        config['environment-profile'] = {'api_key': 'environmentprofilekey'}
        config['blank-profile'] = {}

        # Monkeypatch the user's home directory to be the temp directory
        monkeypatch.setenv('HOME', str(tmp_path))  # Linux/Unix
        monkeypatch.setenv('USERPROFILE', str(tmp_path))  # Windows

        # Create .mlhub directory and config file
        mlhub_dir = tmp_path / '.mlhub'
        mlhub_dir.mkdir()
        config_file = mlhub_dir / 'profiles'
        with config_file.open('w') as dst:
            config.write(dst)

        yield config

    def test_api_key_from_argument(self):
        """The API key given as an init argument is stored on the session."""
        session = get_session(api_key='fromargument')
        assert session.params.get('key') == 'fromargument'

    def test_api_key_from_environment(self, monkeypatch):
        """The API key given by the MLHUB_API_KEY environment variable is stored on the session."""
        monkeypatch.setenv('MLHUB_API_KEY', 'fromenvironment')

        session = get_session()
        assert session.params.get('key') == 'fromenvironment'

    def test_api_key_from_default_profile(self, mock_profile):
        """The API key from the default profile of ~/.mlhub/profiles is stored on the session if no explicit profile is given."""
        session = get_session()
        assert session.params.get('key') == 'defaultapikey'

    def test_api_key_from_named_profile(self, mock_profile):
        """The API key from the given profile in ~/.mlhub/profiles is stored on the session."""
        session = get_session(profile='other-profile')
        assert session.params.get('key') == 'otherapikey'

    def test_api_key_from_environment_named_profile(self, mock_profile, monkeypatch):
        """The API key from the profile given in the MLHUB_PROFILE environment variable is stored on the session."""
        monkeypatch.setenv('MLHUB_PROFILE', 'environment-profile')

        session = get_session()
        assert session.params.get('key') == 'environmentprofilekey'

    def test_user_defined_mlhub_home(self, monkeypatch, tmp_path):
        """If the MLHUB_HOME environment variable is set, the client should look for a profiles file in that directory.
        """
        # Create user-defined home directory
        mlhub_home = tmp_path / 'some-directory' / '.mlhub'
        mlhub_home.mkdir(parents=True)

        # Create profile
        config = configparser.ConfigParser()
        config['default'] = {'api_key': 'userdefinedhome'}

        # Save to profile file
        with (mlhub_home / 'profiles').open('w') as dst:
            config.write(dst)

        # Monkeypatch the MLHUB_HOME variable
        monkeypatch.setenv('MLHUB_HOME', str(mlhub_home.resolve()))

        session = get_session()
        assert session.params.get('key') == 'userdefinedhome'

    def test_from_env_error(self, monkeypatch):
        """Raises an exception if no MLHUB_API_KEY environment variable is found when explicitly loading session from environment."""
        # Ensure there is not MLHUB_API_KEY environment variable
        monkeypatch.delenv('MLHUB_API_KEY', raising=False)

        with pytest.raises(APIKeyNotFound) as excinfo:
            Session.from_env()

        assert 'No "MLHUB_API_KEY" variable found in environment.' == str(excinfo.value)

    def test_no_profiles_file(self, tmp_path, monkeypatch):
        """Raises an exception if no profile files are found when falling back to using profiles."""
        # Ensure there is no profiles file
        config_file = tmp_path / '.mlhub' / 'profiles'
        if config_file.exists():
            config_file.unlink()

        # Monkeypatch the user's home directory to be the temp directory
        monkeypatch.setenv('HOME', str(tmp_path))

        with pytest.raises(APIKeyNotFound) as excinfo:
            Session.from_config()

        assert 'No file found' in str(excinfo.value)

    def test_invalid_profile_name(self, mock_profile):
        """Raises an exception if a non-existent profile name is given."""
        with pytest.raises(APIKeyNotFound) as excinfo:
            Session.from_config(profile='does-not-exist')

        assert 'Could not find "does-not-exist" section' in str(excinfo.value)

    def test_missing_api_key(self, mock_profile):
        """Raises an exception if the profile does not have an api_key value."""
        with pytest.raises(APIKeyNotFound) as excinfo:
            Session.from_config(profile='blank-profile')

        assert 'Could not find "api_key" value in "blank-profile" section' in str(excinfo.value)

    def test_unresolved_api_key(self, monkeypatch, tmp_path):
        """Raises an exception if no API key can be resolved from arguments, environment, or profiles."""
        # Monkeypatch the user's home directory to be the temp directory.
        monkeypatch.setenv('HOME', str(tmp_path))

        # Ensure we don't have any MLHUB_* environment variables set
        monkeypatch.delenv('MLHUB_API_KEY', raising=False)
        monkeypatch.delenv('MLHUB_PROFILE', raising=False)

        # Ensure we don't have a profiles file
        config_file = tmp_path / '.mlhub' / 'profiles'
        if config_file.exists():
            config_file.unlink()

        with pytest.raises(APIKeyNotFound) as excinfo:
            get_session()

        assert 'Could not resolve an API key from arguments, the environment, or a config file.' == str(excinfo.value)


class TestSessionRequests:

    @pytest.fixture(scope='function', autouse=True)
    def test_api_key(self, monkeypatch):
        """Set the default (dummy) API key to use for testing."""
        monkeypatch.setenv('MLHUB_API_KEY', 'testapikey')
        return os.getenv('MLHUB_API_KEY')

    def test_inject_api_key(self, requests_mock, test_api_key):
        """The API key stored on the session is used in requests and any additional query params that are passed in the
        request method are preserved."""

        requests_mock.get('https://some-domain.com', text='{}')

        session = get_session()  # Gets the API key from the monkeypatched environment variable

        # Test injection of API key
        session.get('https://some-domain.com')

        history = requests_mock.request_history

        assert len(history) == 1
        qs = urllib.parse.urlsplit(history[0].url).query
        query_params = urllib.parse.parse_qs(qs)
        assert query_params.get('key') == [test_api_key]

        # Test preservation of other query params
        session.get('https://some-domain.com', params={'otherparam': 'here'})

        history = requests_mock.request_history

        assert len(history) == 2
        qs = urllib.parse.urlsplit(history[1].url).query
        query_params = urllib.parse.parse_qs(qs)
        assert query_params.get('key') == [test_api_key]
        assert query_params.get('otherparam') == ['here']

        # Test overwriting api key in request method
        session.get('https://some-domain.com', params={'key': 'new-api-key'})

        history = requests_mock.request_history

        assert len(history) == 3
        qs = urllib.parse.urlsplit(history[2].url).query
        query_params = urllib.parse.parse_qs(qs)
        assert query_params.get('key') == ['new-api-key']

    def test_inject_headers(self, requests_mock):
        """The session injects the User-Agent and Accept headers."""

        requests_mock.get('https://some-domain.com')

        session = get_session()

        session.get('https://some-domain.com')

        history = requests_mock.request_history
        assert len(history) == 1

        assert history[0].headers.get('accept') == 'application/json'
        assert 'radiant_mlhub/0.2.2' in history[0].headers.get('user-agent')

    def test_relative_path(self, requests_mock):
        """The session uses the default root URL and joins relative paths to the root URL."""

        session = get_session()

        # Without leading slash
        requests_mock.get('https://api.radiant.earth/mlhub/v1/relative/path', text='{}')

        try:
            session.get('relative/path')
            session.get('/relative/path')
        except NoMockAddress as e:
            pytest.fail(f'Unexpected request: {e.request}')

        history = requests_mock.request_history
        assert len(history) == 2
        assert urllib.parse.urlsplit(history[0].url).netloc == 'api.radiant.earth'
        assert urllib.parse.urlsplit(history[0].url).path == '/mlhub/v1/relative/path'
        assert urllib.parse.urlsplit(history[1].url).netloc == 'api.radiant.earth'
        assert urllib.parse.urlsplit(history[1].url).path == '/mlhub/v1/relative/path'

    def test_auth_error(self, requests_mock):
        """The session raises an AuthenticationError if it gets a 401 response."""
        session = get_session(api_key='not-valid')

        requests_mock.get(
            'https://api.radiant.earth/mlhub/v1/auth-error',
            status_code=401,
            reason='UNAUTHORIZED',
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>401 Unauthorized</title>\n'
                 '<h1>Unauthorized</h1>\n<p>The server could not verify that you are authorized to access the URL requested. '
                 'You either supplied the wrong credentials (e.g. a bad password), or your browser doesn\'t understand how to '
                 'supply the credentials required.</p>\n'
        )

        with pytest.raises(AuthenticationError) as excinfo:
            session.get('https://api.radiant.earth/mlhub/v1/auth-error')

        assert 'Authentication failed. API Key: not-valid' == str(excinfo.value)


class TestAnonymousSession:
    @pytest.fixture(scope='function', autouse=True)
    def mock_profile(self):
        pass

    def test_anonymous_session_has_no_key(self):
        """Session instantiated with api_key=None should not include a "key" query parameter."""
        session = Session(api_key=None)
        assert 'key' not in session.params

    def get_anonymous_session(self):
        """get_session called with the anonymouse profile should return a session that does not
        include a "key" query parameter."""
        session = get_session(profile="__anonymous__")
        assert 'key' not in session.params
