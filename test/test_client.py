import os

import pytest
import radiant_mlhub.client
from radiant_mlhub.exceptions import MLHubException, EntityDoesNotExist


class TestClient:

    @pytest.fixture
    def collection_does_not_exist(self, requests_mock):
        endpoint = 'https://api.radiant.earth/mlhub/v1/collections/no_collection'

        requests_mock.get(
            endpoint,
            status_code=404,
            reason='NOT FOUND',
            headers={'Content-Type': 'text/html; charset=utf-8'},
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
                 '<title>404 Not Found</title>\n<h1>Not Found</h1>\n'
                 '<p>The requested URL was not found on the server. '
                 'If you entered the URL manually please check your spelling and try again.</p>\n'
        )

        yield endpoint

    @pytest.fixture
    def dataset_does_not_exist(self, requests_mock):
        endpoint = 'https://api.radiant.earth/mlhub/v1/datasets/no_dataset'

        requests_mock.get(
            endpoint,
            status_code=404,
            reason='NOT FOUND',
            headers={'Content-Type': 'text/html; charset=utf-8'},
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
                 '<title>404 Not Found</title>\n<h1>Not Found</h1>\n'
                 '<p>The requested URL was not found on the server. '
                 'If you entered the URL manually please check your spelling and try again.</p>\n'
        )

        yield endpoint

    @pytest.fixture
    def internal_server_error(self, requests_mock):
        endpoint = 'https://api.radiant.earth/mlhub/v1/collections/internal_error'

        requests_mock.get(
            endpoint,
            status_code=500,
            reason='Internal Server Error',
            headers={'Content-Type': 'text/html; charset=utf-8'},
            text='<html>\n  <head>\n    <title>Internal Server Error</title>\n  '
                 '</head>\n  <body>\n    <h1><p>Internal Server Error</p></h1>\n    \n  </body>\n</html>\n'
        )

        yield endpoint

    def test_collection_does_not_exist(self, collection_does_not_exist):
        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_collection('no_collection')

        assert 'Collection "no_collection" does not exist.' == str(excinfo.value)

    def test_dataset_does_not_exist(self, dataset_does_not_exist):
        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_dataset('no_dataset')

        assert 'Dataset "no_dataset" does not exist.' == str(excinfo.value)

    def test_internal_server_error(self, internal_server_error):
        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.get_collection('internal_error')

        assert 'Internal Server Error' in str(excinfo.value)

    def test_list_collection_items(self, source_collection_items):
        items = list(radiant_mlhub.client.list_collection_items('bigearthnet_v1_source', limit=40))

        assert len(items) == 40
        assert 'assets' in items[0]
        assert items[0]['id'] == 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

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
            headers={'content-type': 'text/html; charset=utf-8'},
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>404 Not Found</title>\n<h1>Not Found</h1>\n' \
                 '<p>The requested URL was not found on the server. '
                 'If you entered the URL manually please check your spelling and try again.</p>'
        )

        with pytest.raises(EntityDoesNotExist):
            radiant_mlhub.client.get_collection_item(
                collection_id,
                item_id
            )

        # Mock 500 response for unknown server error
        requests_mock.get(
            url,
            status_code=500,
            headers={'content-type': 'text/html; charset=utf-8'},
            text=''
        )

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

    def test_download_archive_does_not_exist(self, archive_does_not_exist, tmp_path):
        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.download_archive(archive_does_not_exist, output_dir=tmp_path)

        assert f'Archive "{archive_does_not_exist}" does not exist and may still be generating. ' \
               'Please try again later.' == str(excinfo.value)

    def test_download_exists(self, source_collection_archive, tmp_path):
        expected_output_path = tmp_path / f'{source_collection_archive}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test exist_okay True / no overwrite (default)
        output_path = radiant_mlhub.client.download_archive(source_collection_archive, output_dir=tmp_path)
        assert output_path.stat().st_size == original_size

        # Test overwrite
        output_path = radiant_mlhub.client.download_archive(source_collection_archive, overwrite=True)
        assert output_path.stat().st_size > original_size

        # Test error
        with pytest.raises(FileExistsError):
            radiant_mlhub.client.download_archive(source_collection_archive, exist_okay=False)
