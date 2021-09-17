import os
import pathlib
import re
from urllib.parse import urljoin, parse_qs, urlsplit
from typing import TYPE_CHECKING

import pytest

import radiant_mlhub.client
from radiant_mlhub.exceptions import EntityDoesNotExist, MLHubException, AuthenticationError

if TYPE_CHECKING:
    from requests_mock import Mocker as Mocker_Type


class TestCustomUrl:

    def test_custom_url_list_datasets(self, monkeypatch: pytest.MonkeyPatch, requests_mock: "Mocker_Type") -> None:
        # Set up custom URL
        custom_root_url = "https://staging.api.radiant.earth"
        monkeypatch.setenv('MLHUB_ROOT_URL', custom_root_url)

        # Mock this using requests-mock
        url = 'https://staging.api.radiant.earth/datasets?key=test_key'
        requests_mock.get(url, status_code=200, json=[])

        # Making request to API
        radiant_mlhub.client.list_datasets()

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == "https://staging.api.radiant.earth/datasets?key=test_key"

    def test_custom_url_get_collection(self, monkeypatch: pytest.MonkeyPatch, requests_mock: "Mocker_Type") -> None:
        # Set up custom URL
        custom_root_url = "https://staging.api.radiant.earth"
        monkeypatch.setenv('MLHUB_ROOT_URL', custom_root_url)

        # Mock this using requests-mock
        url = 'https://staging.api.radiant.earth/collections/collection_id?key=test_key'
        requests_mock.get(url, status_code=200, json=[])

        # Making request to API
        radiant_mlhub.client.get_collection("collection_id")

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == "https://staging.api.radiant.earth/collections/collection_id?key=test_key"

    def test_custom_url_list_collection_items(self, monkeypatch: pytest.MonkeyPatch, requests_mock: "Mocker_Type") -> None:
        # Set up custom URL
        custom_root_url = "https://staging.api.radiant.earth"
        monkeypatch.setenv('MLHUB_ROOT_URL', custom_root_url)

        # Mock this using requests-mock
        url = 'https://staging.api.radiant.earth/collections/collection_id/items?key=test_key'
        requests_mock.get(url, status_code=200, json={"features": []})

        # Making request to API
        list(radiant_mlhub.client.list_collection_items("collection_id"))

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == "https://staging.api.radiant.earth/collections/collection_id/items?key=test_key"


class TestClient:

    @pytest.mark.vcr
    def test_collection_does_not_exist(self) -> None:
        collection_id = 'no_collection'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert f'Collection "{collection_id}" does not exist.' == str(excinfo.value)

    def test_dataset_does_not_exist(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        dataset_id = 'no_dataset'

        id_endpoint = urljoin(root_url, f"datasets/{dataset_id}")

        requests_mock.get(id_endpoint, status_code=404)

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_dataset(dataset_id)
        assert f'Dataset "{dataset_id}" does not exist.' == str(excinfo.value)

    def test_internal_server_dataset_error(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        # Mock this using requests-mock instead of VCRPY so we can simulate a 500 response
        dataset_id = 'internal_server_error'
        url = urljoin(root_url, f'datasets/{dataset_id}')
        requests_mock.get(url, status_code=500, reason='Internal Server Error')

        with pytest.raises(MLHubException):
            radiant_mlhub.client.get_dataset(dataset_id)

    def test_internal_server_collections_error(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        collection_id = 'internal_error'
        endpoint = urljoin(root_url, f'collections/{collection_id}')

        requests_mock.get(endpoint, status_code=500, reason='Internal Server Error')
        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.get_collection(collection_id)

        assert 'Internal Server Error' in str(excinfo.value)

    def test_get_dataset_by_doi(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        dataset_doi = "10.6084/m9.figshare.12047478.v2"
        endpoint = urljoin(root_url, f"datasets/doi/{dataset_doi}")
        requests_mock.get(endpoint, status_code=200, json={})

        radiant_mlhub.client.get_dataset_by_doi(dataset_doi)

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(endpoint).path

    def test_get_dataset_by_id(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        dataset_id = "some_dataset"
        endpoint = urljoin(root_url, f"datasets/{dataset_id}")
        requests_mock.get(endpoint, status_code=200, json={})

        radiant_mlhub.client.get_dataset_by_id(dataset_id)

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(endpoint).path

    def test_get_dataset_uses_id_when_appropriate(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        dataset_id = "some_dataset"

        id_endpoint = urljoin(root_url, f"datasets/{dataset_id}")

        requests_mock.get(id_endpoint, status_code=200, json={})

        radiant_mlhub.client.get_dataset(dataset_id)

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(id_endpoint).path

    def test_get_dataset_uses_doi_when_appropriate(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        dataset_doi = "10.6084/m9.figshare.12047478.v2"

        doi_endpoint = urljoin(root_url, f"datasets/doi/{dataset_doi}")

        requests_mock.get(doi_endpoint, status_code=200, json={})

        radiant_mlhub.client.get_dataset(dataset_doi)

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(doi_endpoint).path

    def test_download_archive_only_accepts_dir(self, tmp_path: pathlib.Path) -> None:
        # Test error if file path is provided
        tmp_file = tmp_path / 'test.txt'
        tmp_file.touch()

        with pytest.raises(ValueError):
            radiant_mlhub.client.download_archive('_', output_dir=tmp_file)

    def test_list_dataset_tags_filter(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        escaped_root_url = root_url.replace(".", r"\.")
        route_match = re.compile(f"^{escaped_root_url}datasets")
        requests_mock.get(route_match, status_code=200, text="[]")

        radiant_mlhub.client.list_datasets(tags=["segmentation", "sar"])

        history = requests_mock.request_history
        assert len(history) == 1

        parsed = urlsplit(history[0].url)
        query_params = parse_qs(parsed.query)

        print(history[0].url)
        print(query_params)

        assert "tags" in query_params, "Call to API was missing 'tags' query parameter"
        assert "segmentation" in query_params["tags"], "'segmentation' was not in 'tags' query parameter"
        assert "sar" in query_params["tags"], "'sar' was not in 'tags' query parameter"

    def test_list_dataset_text_filter(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        escaped_root_url = root_url.replace(".", r"\.")
        route_match = re.compile(f"^{escaped_root_url}datasets")
        requests_mock.get(route_match, status_code=200, text="[]")

        radiant_mlhub.client.list_datasets(text=["buildings"])

        history = requests_mock.request_history
        assert len(history) == 1

        parsed = urlsplit(history[0].url)
        query_params = parse_qs(parsed.query)

        assert "text" in query_params, "Call to API was missing 'text' query parameter"
        assert "buildings" in query_params["text"], "'buildings' was not in 'text' query parameter"


class TestClientAuthenticatedEndpoints:

    @pytest.mark.vcr
    def test_list_collection_items(self) -> None:
        items = list(radiant_mlhub.client.list_collection_items('ref_african_crops_kenya_02_source', limit=40))

        assert len(items) == 40
        assert 'assets' in items[0]
        assert items[0]['id'].startswith('ref_african_crops_kenya_02')

        # Test pagination break
        items = list(radiant_mlhub.client.list_collection_items('ref_african_crops_kenya_02_source', limit=100))
        assert len(items) == 52

    @pytest.mark.vcr
    def test_get_collection_item(self) -> None:
        item = radiant_mlhub.client.get_collection_item(
            'ref_african_crops_kenya_02_source',
            'ref_african_crops_kenya_02_tile_02_20190721'
        )

        assert item['id'] == 'ref_african_crops_kenya_02_tile_02_20190721'

    @pytest.mark.vcr
    def test_get_collection_item_errors(self) -> None:
        # Mock 404 response for collection and/or item not existing
        collection_id = 'no_collection'
        item_id = 'item_id'

        with pytest.raises(EntityDoesNotExist):
            radiant_mlhub.client.get_collection_item(
                collection_id,
                item_id
            )

    @pytest.mark.vcr
    def test_download_archive(self, tmp_path: pathlib.Path) -> None:
        # Set CWD to temp path
        os.chdir(tmp_path)

        # Let output_dir default to CWD
        output_path = radiant_mlhub.client.download_archive('ref_african_crops_kenya_02_labels')

        assert output_path == tmp_path / 'ref_african_crops_kenya_02_labels.tar.gz'
        assert output_path.exists()

    @pytest.mark.vcr
    def test_download_archive_does_not_exist(self, tmp_path: pathlib.Path) -> None:
        archive_id = 'no_archive'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.download_archive(archive_id, output_dir=tmp_path)

        assert f'Archive "{archive_id}" does not exist and may still be generating. ' \
               'Please try again later.' == str(excinfo.value)

    @pytest.mark.vcr
    def test_skip_download_exists(self, tmp_path: pathlib.Path) -> None:
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
    def test_overwrite_download_exists(self, tmp_path: pathlib.Path) -> None:
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
    def mock_profile(self) -> None:
        pass

    def test_list_datasets_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        url = urljoin(root_url, 'datasets')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json=[])

        _ = radiant_mlhub.client.list_datasets(profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_datasets_anonymously_works(self) -> None:
        datasets = radiant_mlhub.client.list_datasets(profile="__anonymous__")
        assert len(datasets) > 0

    def test_list_collections_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        url = urljoin(root_url, 'collections')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"collections": []})

        _ = radiant_mlhub.client.list_collections(profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collections_anonymously_works(self) -> None:
        collections = radiant_mlhub.client.list_collections(profile="__anonymous__")
        assert len(collections) > 0

    def test_get_collection_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        collection_id = 'bigearthnet_v1_source'
        url = urljoin(root_url, f'collections/{collection_id}')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={})

        _ = radiant_mlhub.client.get_collection(collection_id, profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_get_collection_anonymously_works(self) -> None:
        collection_id = 'bigearthnet_v1_source'
        collection = radiant_mlhub.client.get_collection(collection_id, profile="__anonymous__")
        assert isinstance(collection, dict)

    def test_list_collection_items_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        collection_id = "bigearthnet_v1_source"
        url = urljoin(root_url, f'collections/{collection_id}/items')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"features": []})

        _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile="__anonymous__"))

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collection_items_anonymously_does_not_work(self) -> None:
        collection_id = "bigearthnet_v1_source"

        with pytest.raises(AuthenticationError) as excinfo:
            _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile="__anonymous__"))

        assert "No API key provided" in str(excinfo.value)
