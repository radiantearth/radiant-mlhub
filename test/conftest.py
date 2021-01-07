import configparser
import pathlib
import json

import pytest


def read_data_file(file_name):
    full_path = pathlib.Path(__file__).parent / 'data' / file_name
    with full_path.open('r') as src:
        return src.read()


@pytest.fixture(scope='function')
def bigearthnet_v1_source(requests_mock):
    """Response for GET /collections/bigearthnet_v1_source."""
    response_text = read_data_file('bigearthnet_v1_source.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source'

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture(scope='function')
def collections_list(requests_mock):
    """Response for GET /collections."""
    collections_response = read_data_file('collections_list.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections'

    requests_mock.get(endpoint, text=collections_response)

    yield endpoint


@pytest.fixture(scope='function')
def bigearthnet_v1_source_items(requests_mock):
    """Mock the response for listing items for the bigearthnet_v1_source collection."""
    items_response_text = read_data_file('bigearthnet_v1_source_items_0.json')
    items_response_dict = json.loads(items_response_text)

    page_2_response_text = read_data_file('bigearthnet_v1_source_items_1.json')

    items_endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source/items'
    page_2_endpoint = items_response_dict['links'][0]['href']  # The "next" link is the only one in this response

    requests_mock.get(items_endpoint, text=items_response_text)
    requests_mock.get(page_2_endpoint, text=page_2_response_text)

    yield items_endpoint


@pytest.fixture(scope='function')
def bigearthnet_v1_source_item(requests_mock):
    """Mock the response for getting getting the first item from the bigearthnet_v1_source collection."""
    response_text = read_data_file('bigearthnet_v1_source_item.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source/items/' \
               'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture(autouse=True)
def mock_profile(monkeypatch, tmp_path):
    config = configparser.ConfigParser()

    config['default'] = {'api_key': 'defaultapikey'}

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
