import os

import pytest
import radiant_mlhub.client
from radiant_mlhub.exceptions import MLHubException, EntityDoesNotExist


class TestClient:

    def test_collection_does_not_exist(self, requests_mock):
        collection_id = 'no_collection'
        url = f'https://api.radiant.earth/mlhub/v1/collections/{collection_id}'

        requests_mock.get(url, status_code=404, reason='NOT FOUND')
        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert f'Collection "{collection_id}" does not exist.' == str(excinfo.value)

    def test_dataset_errors(self, requests_mock):
        # Mock 404
        dataset_id = 'no_dataset'
        url = f'https://api.radiant.earth/mlhub/v1/datasets/{dataset_id}'
        requests_mock.get(url, status_code=404, reason='NOT FOUND')

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_dataset(dataset_id)
        assert f'Dataset "{dataset_id}" does not exist.' == str(excinfo.value)

        # Mock 500
        requests_mock.get(url, status_code=500, reason='Internal Server Error')

        with pytest.raises(MLHubException):
            radiant_mlhub.client.get_dataset(dataset_id)

    def test_internal_server_error(self, requests_mock):
        collection_id = 'internal_error'
        endpoint = f'https://api.radiant.earth/mlhub/v1/collections/{collection_id}'

        requests_mock.get(endpoint, status_code=500, reason='Internal Server Error')
        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert 'Internal Server Error' in str(excinfo.value)

    def test_list_collection_items(self, source_collection_items):
        items = list(radiant_mlhub.client.list_collection_items('bigearthnet_v1_source', limit=40))

        assert len(items) == 40
        assert 'assets' in items[0]
        assert items[0]['id'] == 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

        # Test pagination break
        items = list(radiant_mlhub.client.list_collection_items('bigearthnet_v1_source', limit=500))
        assert len(items) == 60

    def test_get_collection_item(self, source_collection_item):
        item = radiant_mlhub.client.get_collection_item(
            'bigearthnet_v1_source',
            'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'
        )

        assert item['stac_extensions'] == ['eo']
        assert item['id'] == 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

    def test_get_collection_item_errors(self, requests_mock):
        # Mock 404 response for collection and/or item not existing
        collection_id = 'no_collection'
        item_id = 'item_id'
        url = f'https://api.radiant.earth/mlhub/v1/collections/{collection_id}/items/{item_id}'

        requests_mock.get(
            url,
            status_code=404,
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>404 Not Found</title>\n<h1>Not Found</h1>\n'
                 '<p>The requested URL was not found on the server. '
                 'If you entered the URL manually please check your spelling and try again.</p>'
        )

        with pytest.raises(EntityDoesNotExist):
            radiant_mlhub.client.get_collection_item(
                collection_id,
                item_id
            )

        # Mock 500 response for unknown server error
        requests_mock.get(url, status_code=500, text='')

        with pytest.raises(MLHubException):
            radiant_mlhub.client.get_collection_item(
                collection_id,
                item_id
            )

    def test_download_archive(self, source_collection_archive, tmp_path):
        # Set CWD to temp path
        os.chdir(tmp_path)

        # Let output_dir default to CWD
        output_path = radiant_mlhub.client.download_archive(source_collection_archive)

        assert output_path == tmp_path / 'bigearthnet_v1_source.tar.gz'
        assert output_path.exists()

    def test_download_archive_no_bytes(self, collection_archive_no_bytes, tmp_path):
        radiant_mlhub.client.download_archive(collection_archive_no_bytes, output_dir=tmp_path)

        assert (tmp_path / 'bigearthnet_v1_source.tar.gz').exists()

    def test_download_archive_errors(self, requests_mock, tmp_path):
        archive_id = 'no_archive'
        url = f'https://api.radiant.earth/mlhub/v1/archive/{archive_id}'

        # Mock a 404 response from the S3 endpoint (archive does not exist)
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
                 '<a href="https://radiant-mlhub.s3.amazonaws.com/archives/no_archive.tar.gz">'
                 'https://radiant-mlhub.s3.amazonaws.com/archives/no_archive.tar.gz</a>.  If not click the link.'
        )

        # Mock the head requests
        requests_mock.head(
            url,
            status_code=302,
            headers={
                'Content-Type': 'text/html; charset=utf-8',
                'Content-Length': '343',
                'Location': 'https://radiant-mlhub.s3.amazonaws.com/archives/no_archive.tar.gz',
            },
            text=''
        )
        requests_mock.head(
            'https://radiant-mlhub.s3.amazonaws.com/archives/no_archive.tar.gz',
            status_code=404,
            reason='Not Found'
        )

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.download_archive(archive_id, output_dir=tmp_path)

        assert f'Archive "{archive_id}" does not exist and may still be generating. ' \
               'Please try again later.' == str(excinfo.value)

        # Mock an internal server error
        requests_mock.head(url, status_code=500)

        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.download_archive(archive_id)
        # Ensure this is being caught as a generic MLHubException and not the EntityDoesNotExist exception
        assert excinfo.type is not EntityDoesNotExist

        # Test error if file path is provided
        tmp_file = tmp_path / 'test.txt'
        tmp_file.touch()

        with pytest.raises(ValueError):
            radiant_mlhub.client.download_archive(archive_id, output_dir=tmp_file)

    def test_download_exists(self, source_collection_archive, tmp_path):
        expected_output_path = tmp_path / f'{source_collection_archive}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test if_exists = 'skip' (default)
        output_path = radiant_mlhub.client.download_archive(
            source_collection_archive,
            output_dir=tmp_path,
            if_exists='skip'
        )
        assert output_path.stat().st_size == original_size

        # Test overwrite
        output_path = radiant_mlhub.client.download_archive(
            source_collection_archive,
            output_dir=tmp_path,
            if_exists='overwrite'
        )
        assert output_path.stat().st_size > original_size
