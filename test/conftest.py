import re

import pytest
from dotenv import load_dotenv

download_url = re.compile(r'(https?://(?:staging.)?api.radiant.earth/mlhub/v1/download)/[-=\\\w]+/?')


# Scrub any download hashes associated with the API key used during testing
def before_record_response(response):
    response['body']['string'] = re.sub(download_url, r'\1/dummy_hash', response['body']['string'].decode('utf-8'))
    return response


# Filter out the API key from the query parameters
@pytest.fixture(scope='session', autouse=True)
def vcr_config():
    return {'filter_query_parameters': ['key']}


def pytest_recording_configure(config, vcr):
    vcr.before_record_response = before_record_response


@pytest.fixture(scope='module', autouse=True)
def mock_profile():
    load_dotenv()
