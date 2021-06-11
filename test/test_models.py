import json
from pathlib import Path
import pystac
import pytest
from urllib.parse import urljoin, urlsplit, parse_qs

from radiant_mlhub.models import Collection, Dataset
from radiant_mlhub.session import Session


class TestCollection:

    @pytest.mark.vcr
    def test_list_collections(self):
        collections = Collection.list()
        assert isinstance(collections, list)
        assert isinstance(collections[0], Collection)

    @pytest.mark.vcr
    def test_fetch_collection(self):
        collection = Collection.fetch('bigearthnet_v1_source')

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    @pytest.mark.vcr
    def test_get_items_error(self):
        collection = Collection.fetch('bigearthnet_v1_source')

        with pytest.raises(NotImplementedError) as excinfo:
            collection.get_items()

        assert 'For performance reasons, the get_items method has not been implemented for Collection instances. Please ' \
               'use the Collection.download method to download Collection assets.' == str(excinfo.value)

    @pytest.mark.vcr
    def test_fetch_item(self):
        collection = Collection.fetch('ref_african_crops_kenya_02_source')
        item = collection.fetch_item('ref_african_crops_kenya_02_tile_02_20190721')

        assert isinstance(item, pystac.Item)
        assert len(item.assets) == 13

    @pytest.mark.vcr
    def test_download_archive(self, tmp_path):
        collection = Collection.fetch('ref_african_crops_kenya_02_labels')
        output_path = collection.download(output_dir=tmp_path)

        assert output_path == tmp_path / 'ref_african_crops_kenya_02_labels.tar.gz'
        assert output_path.exists()

    @pytest.mark.vcr
    def test_get_registry_url(self):
        collection = Collection.fetch('ref_african_crops_kenya_02_labels')
        assert collection.registry_url == 'https://registry.mlhub.earth/10.34911/rdnt.dw605x'

    @pytest.mark.vcr
    def test_get_registry_url_no_doi(self):
        # Get the example collection as a dict and remove the sci:doi property
        collection_dict = Collection.fetch('ref_african_crops_kenya_02_labels').to_dict()
        collection_dict.pop('sci:doi', None)
        collection = Collection.from_dict(collection_dict)

        assert collection.registry_url is None

    @pytest.mark.vcr
    def test_get_archive_size(self):
        collection = Collection.fetch('bigearthnet_v1_labels')
        assert collection.archive_size == 173029030


class TestAnonymousCollection:
    @pytest.fixture(scope='function', autouse=True)
    def mock_profile(self):
        pass

    def test_list_anonymously_has_no_key(self, requests_mock):
        url = urljoin(Session.ROOT_URL, 'collections')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"collections": []})

        _ = Collection.list(profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    def test_fetch_anonymously_has_no_key(self, requests_mock):
        collection_id = 'bigearthnet_v1_source'
        url = urljoin(Session.ROOT_URL, f'collections/{collection_id}')

        example_collection = Path(__file__).parent / "data" / "bigearthnet_v1_source.json"
        with open(example_collection) as src:
            requests_mock.get(url, json=json.load(src))

        _ = Collection.fetch(collection_id, profile="__anonymous__")

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    def test_fetch_passes_session_to_instance(self, requests_mock):
        collection_id = 'bigearthnet_v1_source'
        collection_url = urljoin(Session.ROOT_URL, f'collections/{collection_id}')

        example_collection = Path(__file__).parent / "data" / "bigearthnet_v1_source.json"
        with open(example_collection) as src:
            requests_mock.get(collection_url, json=json.load(src))

        collection = Collection.fetch(collection_id, profile="__anonymous__")
        assert collection.session_kwargs.get("profile") == "__anonymous__"

    def test_anonymous_archive_size(self, requests_mock):
        collection_id = 'bigearthnet_v1_source'
        example_collection = Path(__file__).parent / "data" / "bigearthnet_v1_source.json"
        with open(example_collection) as src:
            collection = Collection.from_dict(json.load(src), profile="__anonymous__")

        info_url = urljoin(Session.ROOT_URL, f'archive/{collection_id}/info')
        requests_mock.get(info_url, json={})

        _ = collection.archive_size

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs


class TestDataset:

    @pytest.mark.vcr
    def test_list_datasets(self):
        """Dataset.list returns a list of Dataset instances."""
        datasets = Dataset.list()
        assert isinstance(datasets[0], Dataset)

    @pytest.mark.vcr
    def test_fetch_dataset(self):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert isinstance(dataset, Dataset)
        assert dataset.id == 'bigearthnet_v1'
        assert dataset.registry_url == 'https://registry.mlhub.earth/10.14279/depositonce-10149'
        assert dataset.doi == '10.14279/depositonce-10149'
        assert dataset.citation == 'G. Sumbul, M. Charfuelan, B. Demir, V. Markl, \"BigEarthNet: A Large-Scale '\
            'Benchmark Archive for Remote Sensing Image Understanding\", IEEE International Geoscience and Remote '\
            'Sensing Symposium, pp. 5901-5904, Yokohama, Japan, 2019.'

    # https://github.com/kevin1024/vcrpy/issues/295
    @pytest.mark.vcr
    @pytest.mark.skip(reason="vcrpy does not handle multithreaded requests.")
    def test_dataset_collections(self):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert len(dataset.collections) == 2
        assert len(dataset.collections.source_imagery) == 1
        assert len(dataset.collections.labels) == 1
        assert all(isinstance(c, Collection) for c in dataset.collections)
        assert dataset.collections[0] in dataset.collections.source_imagery

    @pytest.mark.vcr
    @pytest.mark.skip(reason="Download size is to large to store in cassette.")
    def test_download_collection_archives(self, tmp_path):
        dataset = Dataset.fetch('ref_african_crops_kenya_02')
        output_paths = dataset.download(output_dir=tmp_path)

        assert len(output_paths) == 2
        assert all(p.exists() for p in output_paths)

    # https://github.com/kevin1024/vcrpy/issues/295
    @pytest.mark.vcr
    @pytest.mark.skip(reason="vcrpy does not handle multithreaded requests.")
    def test_collections_list(self):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert dataset.collections.__repr__() == '[<Collection id=bigearthnet_v1_source>, <Collection id=bigearthnet_v1_labels>]'

    @pytest.mark.vcr
    @pytest.mark.skip(reason="vcrpy does not handle multithreaded requests.")
    def test_total_archive_size(self):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert dataset.total_archive_size == 71311240007


class TestAnonymousDataset:
    @pytest.fixture(scope='function', autouse=True)
    def mock_profile(self):
        pass


class TestDatasetNoProfile:
    DATASET = {
        "citation": "Fake citation",
        "collections": [
            {
                "id": "test_collection",
                "types": [
                    "source_imagery"
                ]
            }
        ],
        "doi": "10.12345/depositonce-12345",
        "id": "test_dataset",
        "registry": "https://registry.mlhub.earth/10.12345/depositonce-12345",
        "title": "Test Dataset"
    }

    COLLECTION = {
        "description": "Test Collection",
        "extent": {
            "spatial": {
                "bbox": [
                    [
                        -9.00023345437725, 1.7542686833884724,
                        83.44558248555553, 68.02168200047284
                    ]
                ]
            },
            "temporal": {
                "interval": [
                    [
                        "2017-06-13T10:10:31Z",
                        "2018-05-29T11:54:01Z"
                    ]
                ]
            }
        },
        "id": "test_collection",
        "links": [],
        "license": "Test License",
        "properties": {},
        "stac_version": "1.0.0-beta.2"
    }

    @pytest.fixture(scope='function', autouse=True)
    def mock_profile(self, monkeypatch, tmp_path):
        """Overwrite the fixture in conftest so we don't set up an API key here"""

        # Monkeypatch the user's home directory to be the temp directory
        # This prevents the client from automatically finding any profiles configured in the user's
        # home directory.
        monkeypatch.setenv('HOME', str(tmp_path))  # Linux/Unix
        monkeypatch.setenv('USERPROFILE', str(tmp_path))  # Windows

        yield

    def test_fetch_with_api_key(self, requests_mock):
        """The Dataset class should use any API keys passed to Dataset.fetch in methods on the
        resulting Dataset instance."""
        dataset_id = self.DATASET["id"]
        collection_id = self.COLLECTION["id"]
        api_key = 'test_api_key'

        dataset_url = urljoin(Session.ROOT_URL, f'datasets/{dataset_id}')
        requests_mock.get(dataset_url, json=self.DATASET)

        collection_url = urljoin(Session.ROOT_URL, f'collections/{collection_id}')
        requests_mock.get(collection_url, json=self.COLLECTION)

        dataset = Dataset.fetch(dataset_id, api_key=api_key)
        _ = dataset.collections

        history = requests_mock.request_history
        assert len(history) == 2
        assert f"key={api_key}" in history[1].url

    def test_list_with_api_key(self, requests_mock):
        """The Dataset class should use any API keys passed to Dataset.list in methods on the
        resulting dataset instances."""

        collection_id = self.COLLECTION["id"]
        api_key = 'test_api_key'

        dataset_url = urljoin(Session.ROOT_URL, 'datasets')
        requests_mock.get(dataset_url, json=[self.DATASET])

        collection_url = urljoin(Session.ROOT_URL, f'collections/{collection_id}')
        requests_mock.get(collection_url, json=self.COLLECTION)

        datasets = Dataset.list(api_key=api_key)
        for dataset in datasets:
            _ = dataset.collections

        history = requests_mock.request_history
        assert len(history) == 2
        assert f"key={api_key}" in history[1].url
