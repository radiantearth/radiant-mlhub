import configparser
import pathlib
import json

import pytest


def read_data_file(file_name, mode='r'):
    full_path = pathlib.Path(__file__).parent / 'data' / file_name
    with full_path.open(mode) as src:
        return src.read()


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


@pytest.fixture(scope='function')
def source_collection(requests_mock):
    """Response for GET /collections/bigearthnet_v1_source."""
    response_text = read_data_file('bigearthnet_v1_source.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source'

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture(scope='function')
def labels_collection(requests_mock):
    """Response for GET /collections/bigearthnet_v1_labels."""
    response_text = read_data_file('bigearthnet_v1_labels.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_labels'

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture
def dataset(requests_mock):
    """Response for GET /datasets/bigearthnet_v1."""
    dataset_id = 'bigearthnet_v1'
    response_text = read_data_file('bigearthnet_v1_dataset.json')
    endpoint = f'https://api.radiant.earth/mlhub/v1/datasets/{dataset_id}'

    requests_mock.get(endpoint, text=response_text)

    yield dataset_id


@pytest.fixture
def datasets(requests_mock):
    """Response for GET /datasets."""
    response_text = read_data_file('datasets_list.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/datasets'

    requests_mock.get('https://api.radiant.earth/mlhub/v1/datasets', text=response_text)

    yield endpoint


@pytest.fixture(scope='function')
def collections(requests_mock):
    """Response for GET /collections."""
    collections_response = read_data_file('collections_list.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections'

    requests_mock.get(endpoint, text=collections_response)

    yield endpoint


@pytest.fixture(scope='function')
def source_collection_items(requests_mock):
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
def source_collection_item(requests_mock):
    """Mock the response for getting getting the first item from the bigearthnet_v1_source collection."""
    response_text = read_data_file('bigearthnet_v1_source_item.json')
    endpoint = 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source/items/' \
               'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

    requests_mock.get(endpoint, text=response_text)

    yield endpoint


@pytest.fixture
def source_collection_archive(requests_mock):
    archive_id = 'bigearthnet_v1_source'
    url = f'https://api.radiant.earth/mlhub/v1/archive/{archive_id}'

    # Mock the initial endpoint
    requests_mock.get(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        },
        text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n<h1>Redirecting...</h1>\n'
             '<p>You should be redirected automatically to target URL: '
             '<a href="https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz">'
             'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz</a>.  If not click the link.'
    )

    # Mock the head requests
    requests_mock.head(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        },
        text=''
    )
    requests_mock.head(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '10000000'
        },
        text=''
    )

    # Mock the first byte range of the download content
    content = read_data_file('bigearthnet_v1_source.first.tar.gz', 'rb')
    requests_mock.get(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        status_code=200,
        request_headers={
          'Range': 'bytes=0-4999999'
        },
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '5000000',
        },
        content=content
    )

    # Mock the second byte range of the download content
    content = read_data_file('bigearthnet_v1_source.second.tar.gz', 'rb')
    requests_mock.get(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        status_code=200,
        request_headers={
            'Range': 'bytes=5000000-9999999'
        },
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '5000000',
        },
        content=content
    )

    yield archive_id


@pytest.fixture
def labels_collection_archive(requests_mock):
    archive_id = 'bigearthnet_v1_labels'
    url = f'https://api.radiant.earth/mlhub/v1/archive/{archive_id}'

    # Mock the initial endpoint
    requests_mock.get(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz',
        },
        text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n<h1>Redirecting...</h1>\n'
             '<p>You should be redirected automatically to target URL: '
             '<a href="https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz">'
             'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz</a>.  If not click the link.'
    )

    # Mock the head requests
    requests_mock.head(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz',
        },
        text=''
    )
    requests_mock.head(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz',
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '10000000'
        },
        text=''
    )

    # Mock the first byte range of the download content
    content = read_data_file('bigearthnet_v1_labels.first.tar.gz', 'rb')
    requests_mock.get(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz',
        status_code=200,
        request_headers={
          'Range': 'bytes=0-4999999'
        },
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '5000000',
        },
        content=content
    )

    # Mock the second byte range of the download content
    content = read_data_file('bigearthnet_v1_labels.second.tar.gz', 'rb')
    requests_mock.get(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_labels.tar.gz',
        status_code=200,
        request_headers={
            'Range': 'bytes=5000000-9999999'
        },
        headers={
            'Accept-Ranges': 'bytes',
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '5000000',
        },
        content=content
    )

    yield archive_id


@pytest.fixture
def collection_archive_no_bytes(requests_mock):
    archive_id = 'bigearthnet_v1_source'
    url = f'https://api.radiant.earth/mlhub/v1/archive/{archive_id}'

    # Mock the initial endpoint
    requests_mock.get(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        },
        text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>Redirecting...</title>\n<h1>Redirecting...</h1>\n'
             '<p>You should be redirected automatically to target URL: '
             '<a href="https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz">'
             'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz</a>.  If not click the link.'
    )

    # Mock the head requests
    requests_mock.head(
        url,
        status_code=302,
        headers={
            'Content-Type': 'text/html; charset=utf-8',
            'Content-Length': '343',
            'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        },
        text=''
    )
    requests_mock.head(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        headers={
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '10000000'
        },
        text=''
    )

    # Mock the full download content
    content = read_data_file('bigearthnet_v1_source.first.tar.gz', 'rb') + read_data_file('bigearthnet_v1_source.first.tar.gz', 'rb')
    requests_mock.get(
        'https://radiant-mlhub.s3.amazonaws.com/archives/bigearthnet_v1_source.tar.gz',
        status_code=200,
        headers={
            'Content-Type': 'binary/octet-stream',
            'Content-Length': '10000000',
        },
        content=content
    )

    yield archive_id
