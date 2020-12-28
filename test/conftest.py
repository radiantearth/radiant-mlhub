import json
import pathlib
import urllib.parse

import pytest


def read_data_file(file_name):
    full_path = pathlib.Path(__file__).parent / 'data' / file_name
    with full_path.open('r') as src:
        return src.read()


@pytest.fixture(scope='function')
def bigearthnet_v1_source(requests_mock):
    """Mock the response for getting the bigearthnet_v1_source collection."""
    response_text = read_data_file('bigearthnet_v1_source.json')
    endpoint = urllib.parse.urljoin('https://api.radiant.earth/mlhub/v1/', 'collections/bigearthnet_v1_source')

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture(scope='function')
def bigearthnet_v1_source_items(requests_mock):
    """Mock the response for getting the bigearthnet_v1_source collection."""
    items_response_text = read_data_file('bigearthnet_v1_source_items_0.json')
    items_response_dict = json.loads(items_response_text)

    page_2_response_text = read_data_file('bigearthnet_v1_source_items_1.json')

    items_endpoint = urllib.parse.urljoin('https://api.radiant.earth/mlhub/v1/', 'collections/bigearthnet_v1_source/items')
    page_2_endpoint = items_response_dict['links'][0]['href']  # The "next" link is the only one in this response

    requests_mock.get(items_endpoint, text=items_response_text)
    requests_mock.get(page_2_endpoint, text=page_2_response_text)

    yield items_endpoint
