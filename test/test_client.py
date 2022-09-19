import os
import pathlib
import re
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urljoin, urlsplit

import pytest
import radiant_mlhub.client
from dateutil.parser import parse as date_parser
from radiant_mlhub.client.datetime_utils import (one_to_one_check,
                                                 one_to_range_check,
                                                 range_to_range_check)
from radiant_mlhub.exceptions import (AuthenticationError, EntityDoesNotExist,
                                      MLHubException)
from radiant_mlhub.session import ANONYMOUS_PROFILE

if TYPE_CHECKING:
    from requests_mock import Mocker as Mocker_Type


class TestCustomUrl:

    @pytest.fixture(autouse=True)
    def test_api_key(self, monkeypatch: pytest.MonkeyPatch) -> str:
        """Set the default (dummy) API key to use for testing."""
        monkeypatch.setenv('MLHUB_API_KEY', 'testapikey')
        return os.environ['MLHUB_API_KEY']

    @pytest.fixture(autouse=True)
    def custom_root_url(self, monkeypatch: pytest.MonkeyPatch) -> str:
        """Set the custom root url to something other than staging.api.radiant.earth
        (which is the default)"""
        monkeypatch.setenv('MLHUB_ROOT_URL', 'https://custom.api.radiant.earth')
        return os.environ['MLHUB_ROOT_URL']

    def test_custom_url_list_datasets(
            self,
            requests_mock: "Mocker_Type",
            custom_root_url: str,
            test_api_key: str) -> None:
        # Mock this using requests-mock
        expect_url = f'{custom_root_url}/datasets?key={test_api_key}'
        requests_mock.get(expect_url, status_code=200, json=[])

        # Making request to API
        radiant_mlhub.client.list_datasets(api_key=test_api_key)

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == expect_url

    def test_custom_url_get_collection(
                self,
                requests_mock: "Mocker_Type",
                custom_root_url: str,
                test_api_key: str
            ) -> None:
        # Mock this using requests-mock
        expect_url = f'{custom_root_url}/collections/collection_id?key={test_api_key}'
        requests_mock.get(expect_url, status_code=200, json=[])

        # Making request to API
        radiant_mlhub.client.get_collection("collection_id", api_key=test_api_key)

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == expect_url

    def test_custom_url_list_collection_items(
                self,
                requests_mock: "Mocker_Type",
                custom_root_url: str,
                test_api_key: str
            ) -> None:
        # Mock this using requests-mock
        expect_url = f'{custom_root_url}/collections/collection_id/items?key={test_api_key}'
        requests_mock.get(expect_url, status_code=200, json={"features": []})

        # Making request to API
        list(radiant_mlhub.client.list_collection_items(
            "collection_id", api_key=test_api_key
        ))

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == expect_url

    def test_custom_url_list_ml_models(
        self,
        requests_mock: "Mocker_Type",
        custom_root_url: str,
        test_api_key: str
    ) -> None:
        # Mock this using requests-mock
        expect_url = f'{custom_root_url}/models?key={test_api_key}'
        requests_mock.get(expect_url, status_code=200, json=[])

        # Making request to API
        radiant_mlhub.client.list_models(api_key=test_api_key)

        # Get request history and check that request was made to custom URL
        history = requests_mock.request_history
        assert len(history) == 1
        assert history[0].url == expect_url


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

    def test_ml_model_does_not_exist(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        ml_model_id = 'no_ml_model'

        id_endpoint = urljoin(root_url, f"models/{ml_model_id}")

        requests_mock.get(id_endpoint, status_code=404)

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.get_model_by_id(ml_model_id)
        assert f'MLModel "{ml_model_id}" does not exist.' == str(excinfo.value)

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

    def test_internal_server_ml_model_error(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        # Mock this using requests-mock instead of VCRPY so we can simulate a 500 response
        ml_model_id = 'internal_server_error'
        url = urljoin(root_url, f'models/{ml_model_id}')
        requests_mock.get(url, status_code=500, reason='Internal Server Error')

        with pytest.raises(MLHubException):
            radiant_mlhub.client.get_model_by_id(ml_model_id)

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

    def test_download_collection_archive_only_accepts_dir(self, tmp_path: pathlib.Path) -> None:
        # Test error if file path is provided
        tmp_file = tmp_path / 'test.txt'
        tmp_file.touch()

        with pytest.raises(ValueError):
            radiant_mlhub.client.download_collection_archive('_', output_dir=tmp_file)

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

    def test_get_ml_model_by_id(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        ml_model_id = "some_ml_model"
        endpoint = urljoin(root_url, f"models/{ml_model_id}")
        requests_mock.get(endpoint, status_code=200, json={})

        radiant_mlhub.client.get_model_by_id(ml_model_id)

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(endpoint).path

    def test_list_ml_models(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        endpoint = urljoin(root_url, "models")
        requests_mock.get(endpoint, status_code=200, json={})
        radiant_mlhub.client.list_models()

        history = requests_mock.request_history

        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(endpoint).path


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
    def test_download_collection_archive(self, tmp_path: pathlib.Path) -> None:
        # Set CWD to temp path
        os.chdir(tmp_path)

        # Let output_dir default to CWD
        output_path = radiant_mlhub.client.download_collection_archive('ref_african_crops_kenya_02_labels')

        assert output_path == tmp_path / 'ref_african_crops_kenya_02_labels.tar.gz'
        assert output_path.exists()

    @pytest.mark.vcr
    def test_download_collection_archive_does_not_exist(self, tmp_path: pathlib.Path) -> None:
        archive_id = 'no_archive'

        with pytest.raises(EntityDoesNotExist) as excinfo:
            radiant_mlhub.client.download_collection_archive(archive_id, output_dir=tmp_path)

        assert f'Archive "{archive_id}" does not exist and may still be generating. ' \
               'Please try again later.' == str(excinfo.value)

    @pytest.mark.vcr
    def test_skip_download_collection_archive_exists(self, tmp_path: pathlib.Path) -> None:
        collection_id = 'ref_african_crops_kenya_02_labels'
        expected_output_path = tmp_path / f'{collection_id}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test if_exists = 'skip' (default)
        output_path = radiant_mlhub.client.download_collection_archive(
            collection_id,
            output_dir=tmp_path,
            if_exists='skip'
        )
        assert output_path.stat().st_size == original_size

    @pytest.mark.vcr
    def test_overwrite_download_collection_archive_exists(self, tmp_path: pathlib.Path) -> None:
        collection_id = 'ref_african_crops_kenya_02_labels'
        expected_output_path = tmp_path / f'{collection_id}.tar.gz'
        expected_output_path.touch(exist_ok=True)
        original_size = expected_output_path.stat().st_size

        # Test overwrite
        output_path = radiant_mlhub.client.download_collection_archive(
            collection_id,
            output_dir=tmp_path,
            if_exists='overwrite'
        )
        assert output_path.stat().st_size > original_size


class TestAnonymousClient:

    @pytest.fixture(autouse=True)
    def make_anonymous_profile(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The MLHUB_API_KEY overrides the anonymous profile."""
        monkeypatch.delenv('MLHUB_API_KEY', raising=False)

    def test_list_datasets_anonymously_has_no_key(
            self,
            requests_mock: "Mocker_Type",
            root_url: str) -> None:
        expect_url = urljoin(root_url, 'datasets')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(expect_url, json=[])

        _ = radiant_mlhub.client.list_datasets(profile=ANONYMOUS_PROFILE)

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_datasets_anonymously_works(self) -> None:
        datasets = radiant_mlhub.client.list_datasets(profile=ANONYMOUS_PROFILE)
        assert len(datasets) > 0

    def test_list_collections_anonymously_has_no_key(
            self,
            requests_mock: "Mocker_Type",
            root_url: str) -> None:
        expect_url = urljoin(root_url, 'collections')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(expect_url, json={"collections": []})

        _ = radiant_mlhub.client.list_collections(profile=ANONYMOUS_PROFILE)

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collections_anonymously_works(self) -> None:
        collections = radiant_mlhub.client.list_collections(profile=ANONYMOUS_PROFILE)
        assert len(collections) > 0

    def test_get_collection_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        collection_id = 'bigearthnet_v1_source'
        expect_url = urljoin(root_url, f'collections/{collection_id}')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(expect_url, json={})

        _ = radiant_mlhub.client.get_collection(collection_id, profile=ANONYMOUS_PROFILE)

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_get_collection_anonymously_works(self) -> None:
        collection_id = 'bigearthnet_v1_source'
        collection = radiant_mlhub.client.get_collection(collection_id, profile=ANONYMOUS_PROFILE)
        assert isinstance(collection, dict)

    def test_list_collection_items_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        collection_id = "bigearthnet_v1_source"
        expect_url = urljoin(root_url, f'collections/{collection_id}/items')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(expect_url, json={"features": []})

        _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile=ANONYMOUS_PROFILE))

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.vcr
    def test_list_collection_items_anonymously_does_not_work(self) -> None:
        collection_id = "bigearthnet_v1_source"

        with pytest.raises(AuthenticationError) as excinfo:
            _ = list(radiant_mlhub.client.list_collection_items(collection_id, profile=ANONYMOUS_PROFILE))

        assert "No API key provided" in str(excinfo.value)

    @pytest.mark.vcr
    def test_list_ml_models_anonymously_works(self) -> None:
        ml_models = radiant_mlhub.client.list_models(profile=ANONYMOUS_PROFILE)
        assert len(ml_models) > 0


class TestDatetimeUtils:

    example_date_from_stac_spec = date_parser('2020-12-11T22:38:32.125000Z')

    def test_one_to_one_check(self):

        # not-identical case
        dt_1 = self.example_date_from_stac_spec
        dt_2 = datetime.now(timezone.utc)
        assert one_to_one_check(dt_1, dt_2) is False

        # identical case
        dt_1 = self.example_date_from_stac_spec
        dt_2 = self.example_date_from_stac_spec
        assert one_to_one_check(dt_1, dt_2) is True

    def test_one_to_range_check(self):

        # non-overlapping case
        dt_1 = datetime.now(timezone.utc)
        range_start = dt_1 + timedelta(weeks=1)
        range_end = dt_1 + timedelta(weeks=2)
        dt_range = (range_start, range_end)
        assert one_to_range_check(dt_1, dt_range) is False

        # overlapping case
        dt_1 = self.example_date_from_stac_spec + timedelta(weeks=1)
        range_start = self.example_date_from_stac_spec
        range_end = self.example_date_from_stac_spec + timedelta(weeks=2)
        dt_range = (range_start, range_end)
        assert one_to_range_check(dt_1, dt_range) is True

        # check boundary case (date happens to equal end date of range)
        dt_1 = datetime.now(timezone.utc)
        range_start = self.example_date_from_stac_spec
        range_end = dt_1
        dt_range = (range_start, range_end)
        assert one_to_range_check(dt_1, dt_range) is True

    def test_range_to_range_check(self):

        # non-overlapping case
        d = self.example_date_from_stac_spec
        range1_start = d - timedelta(weeks=2)
        range1_end = d - timedelta(weeks=1)
        dt_range1 = (range1_start, range1_end)
        range2_start = d + timedelta(weeks=8)
        range2_end = d + timedelta(weeks=9)
        dt_range2 = (range2_start, range2_end)
        assert range_to_range_check(dt_range1, dt_range2) is False

        # overlapping case
        d = self.example_date_from_stac_spec
        range1_start = d + timedelta(weeks=8)
        range1_end = d + timedelta(weeks=9)
        dt_range1 = (range1_start, range1_end)
        range2_start = d + timedelta(weeks=7)
        range2_end = d + timedelta(weeks=10)
        dt_range2 = (range2_start, range2_end)
        assert range_to_range_check(dt_range1, dt_range2) is True

        # check boundary case (start of range happens to equal end of other range)
        d = self.example_date_from_stac_spec
        range1_start = d + timedelta(weeks=8)
        range1_end = d + timedelta(weeks=9)
        dt_range1 = (range1_start, range1_end)
        range2_start = d + timedelta(weeks=9)
        range2_end = d + timedelta(weeks=10)
        dt_range2 = (range2_start, range2_end)
        assert range_to_range_check(dt_range1, dt_range2) is True
