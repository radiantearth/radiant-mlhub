import os
from radiant_mlhub.session import Session
from urllib.parse import urljoin, parse_qs, urlsplit

import pytest

import radiant_mlhub.client
from radiant_mlhub.exceptions import EntityDoesNotExist, MLHubException, AuthenticationError


class TestClient:

    @pytest.mark.vcr
    def test_collection_does_not_exist(self):
        collection_id = 'no_collection'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert f'Collection "{collection_id}" does not exist.' == str(excinfo.value)

    @pytest.mark.vcr
    def test_dataset_does_not_exist(self):
        dataset_id = 'no_dataset'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_dataset(dataset_id)
        assert f'Dataset "{dataset_id}" does not exist.' == str(excinfo.value)

    def test_internal_server_dataset_error(self, requests_mock):
        # Mock this using requests-mock instead of VCRPY so we can simulate a 500 response
        dataset_id = 'internal_server_error'
        url = f'https://api.radiant.earth/mlhub/v1/datasets/{dataset_id}'
        requests_mock.get(url, status_code=500, reason='Internal Server Error')

        with pytest.raises(MLHubException):
            radiant_mlhub.client.get_dataset(dataset_id)

    def test_internal_server_collections_error(self, requests_mock):
        collection_id = 'internal_error'
        endpoint = f'https://api.radiant.earth/mlhub/v1/collections/{collection_id}'

        requests_mock.get(endpoint, status_code=500, reason='Internal Server Error')
        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert 'Internal Server Error' in str(excinfo.value)

    @pytest.mark.vcr
    def test_list_collection_items(self):
        items = list(radiant_mlhub.client.list_collection_items('ref_african_crops_kenya_02_source', limit=40))

        assert len(items) == 40
        assert 'assets' in items[0]
        assert items[0]['id'] == 'ref_african_crops_kenya_02_tile_02_20190721'

        # Test pagination break
        items = list(radiant_mlhub.client.list_collection_items('ref_african_crops_kenya_02_source', limit=100))
        assert len(items) == 52

    @pytest.mark.vcr
    def test_get_collection_item(self):
        item = radiant_mlhub.client.get_collection_item(
            'ref_african_crops_kenya_02_source',
            'ref_african_crops_kenya_02_tile_02_20190721'
        )

        assert item['id'] == 'ref_african_crops_kenya_02_tile_02_20190721'

    @pytest.mark.vcr
    def test_get_collection_item_errors(self):
        # Mock 404 response for collection and/or item not existing
        collection_id = 'no_collection'
        item_id = 'item_id'

        with pytest.raises(EntityDoesNotExist):
            radiant_mlhub.client.get_collection_item(
                collection_id,
                item_id
            )

    @pytest.mark.vcr
    def test_download_archive(self, tmp_path):
        # Set CWD to temp path
        os.chdir(tmp_path)

        # Let output_dir default to CWD
        output_path = radiant_mlhub.client.download_archive('ref_african_crops_kenya_02_labels')

        assert output_path == tmp_path / 'ref_african_crops_kenya_02_labels.tar.gz'
        assert output_path.exists()

    @pytest.mark.vcr
    def test_download_archive_does_not_exist(self, tmp_path):
        archive_id = 'no_archive'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.download_archive(archive_id, output_dir=tmp_path)

        assert f'Archive "{archive_id}" does not exist and may still be generating. ' \
               'Please try again later.' == str(excinfo.value)

    def test_download_archive_only_accepts_dir(self, tmp_path):
        # Test error if file path is provided
        tmp_file = tmp_path / 'test.txt'
        tmp_file.touch()

        with pytest.raises(ValueError):
            radiant_mlhub.client.download_archive('_', output_dir=tmp_file)

    @pytest.mark.vcr
    def test_skip_download_exists(self, tmp_path):
        collection_id = 'ref_african_crops_kenya_02_labels'
        expected_output_path = tmp_path / f'{collection_id}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test if_exists = 'skip' (default)
        output_path = radiant_mlhub.client.download_archive(
            collection_id,
            output_dir=tmp_path,
            if_exists='skip'
        )
        assert output_path.stat().st_size == original_size

    @pytest.mark.vcr
    def test_overwrite_download_exists(self, tmp_path):
        collection_id = 'ref_african_crops_kenya_02_labels'
        expected_output_path = tmp_path / f'{collection_id}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test overwrite
        output_path = radiant_mlhub.client.download_archive(
            collection_id,
            output_dir=tmp_path,
            if_exists='overwrite'
        )
        assert output_path.stat().st_size > original_size


class TestAnonymousClient:
    @pytest.fixture(scope='function', autouse=True)
    def mock_profile(self):
        pass

    def test_list_datasets_anonymously_has_no_key(self, requests_mock):
        url = urljoin(Session.ROOT_URL, 'datasets')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json=[])

        _ = radiant_mlhub.client.list_datasets(profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_datasets_anonymously_works(self):
        datasets = radiant_mlhub.client.list_datasets(profile="__anonymous__")
        assert len(datasets) > 0

    def test_list_collections_anonymously_has_no_key(self, requests_mock):
        url = urljoin(Session.ROOT_URL, 'collections')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"collections": []})

        _ = radiant_mlhub.client.list_collections(profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collections_anonymously_works(self):
        collections = radiant_mlhub.client.list_collections(profile="__anonymous__")
        assert len(collections) > 0

    def test_get_collection_anonymously_has_no_key(self, requests_mock):
        collection_id = 'bigearthnet_v1_source'
        url = urljoin(Session.ROOT_URL, f'collections/{collection_id}')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={})

        _ = radiant_mlhub.client.get_collection(collection_id, profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_get_collection_anonymously_works(self):
        collection_id = 'bigearthnet_v1_source'
        collection = radiant_mlhub.client.get_collection(collection_id, profile="__anonymous__")
        assert isinstance(collection, dict)

    def test_list_collection_items_anonymously_has_no_key(self, requests_mock):
        collection_id = "bigearthnet_v1_source"
        url = urljoin(Session.ROOT_URL, f'collections/{collection_id}/items')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"features": []})

        _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile="__anonymous__"))

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collection_items_anonymously_does_not_work(self):
        collection_id = "bigearthnet_v1_source"

        with pytest.raises(AuthenticationError) as excinfo:
            _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile="__anonymous__"))

        assert "No API key provided" in str(excinfo.value)
