import os
import re
from typing import Any, Dict

import pytest
from pathlib import Path

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
    monkeypatch.setenv('MLHUB_API_KEY', os.getenv("MLHUB_API_KEY") or 'test_key')


@pytest.fixture(scope="function", autouse=True)
def root_url(monkeypatch: pytest.MonkeyPatch) -> str:
    root_url = os.getenv(
        "MLHUB_ROOT_URL",
        "https://staging.api.radiant.earth/mlhub/v1/"
    )
    monkeypatch.setenv("MLHUB_ROOT_URL", root_url)
    return root_url


@pytest.fixture
def stac_mock_json(request) -> str:
    """
    Reads a mocked api response from data/**/*.json files.
    """
    dataset_mark = request.node.get_closest_marker('dataset_id')
    collection_mark = request.node.get_closest_marker('collection_id')
    mock_data_dir = Path(__file__).parent / 'data'
    if dataset_mark is not None:
        (dataset_id, ) = dataset_mark.args
        response_path = mock_data_dir / 'datasets' / f'{dataset_id}.json'
    elif collection_mark is not None:
        (collection_id, ) = collection_mark.args
        response_path = mock_data_dir / 'collections' / f'{collection_id}.json'
    else:
        assert False, 'pytest fixture stac_mock_json is misconfigured.'
    with response_path.open(encoding='utf-8') as src:
        return src.read()
