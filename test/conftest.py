import re
from typing import Any, Dict

import pytest
from dotenv import dotenv_values

download_url = re.compile(r'(https?://(?:staging.)?api.radiant.earth/mlhub/v1/download)/[-=\\\w]+/?')


# Scrub any download hashes associated with the API key used during testing
def before_record_response(response: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response['body']['string'] = re.sub(download_url, r'\1/dummy_hash', response['body']['string'].decode('utf-8')).encode('utf-8')
    except UnicodeDecodeError:
        pass
    return response


# Filter out the API key from the query parameters
@pytest.fixture(scope='module', autouse=True)
def vcr_config() -> Dict[str, Any]:
    return {'filter_query_parameters': ['key']}


@pytest.fixture(scope='function', autouse=True)
def mock_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    denv = dotenv_values()
    monkeypatch.setenv('MLHUB_API_KEY', denv.get('MLHUB_API_KEY') or 'test_key')
