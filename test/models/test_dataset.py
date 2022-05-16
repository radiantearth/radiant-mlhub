import hashlib
import json
import re
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Iterator, cast
from urllib.parse import parse_qs, urljoin, urlsplit

import pytest
from dateutil.parser import parse
from radiant_mlhub.models import Dataset

if TYPE_CHECKING:
    from pathlib import Path as Path_Type

    from requests_mock import Mocker as Mocker_Type


class TestDataset:
    """
    Note: all of the test_download_* methods don't actually download assets.
    See comments in catalog_downloader.py.
    """
    @pytest.mark.vcr
    def test_list_datasets(self) -> None:
        """Dataset.list returns a list of Dataset instances."""
        datasets = Dataset.list()
        assert isinstance(datasets[0], Dataset)

    def test_list_datasets_tags_filter(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        escaped_root_url = root_url.replace(".", r"\.")
        route_match = re.compile(f"^{escaped_root_url}datasets")
        requests_mock.get(route_match, status_code=200, text="[]")

        Dataset.list(tags=["segmentation", "sar"])

        history = requests_mock.request_history
        assert len(history) == 1

        parsed = urlsplit(history[0].url)
        query_params = parse_qs(parsed.query)

        assert "tags" in query_params, "Call to API was missing 'tags' query parameter"
        assert "segmentation" in query_params["tags"], "'segmentation' was not in 'tags' query parameter"
        assert "sar" in query_params["tags"], "'sar' was not in 'tags' query parameter"

    def test_list_datasets_text_filter(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        escaped_root_url = root_url.replace(".", r"\.")
        route_match = re.compile(f"^{escaped_root_url}datasets")
        requests_mock.get(route_match, status_code=200, text="[]")

        Dataset.list(text="buildings")

        history = requests_mock.request_history
        assert len(history) == 1

        parsed = urlsplit(history[0].url)
        query_params = parse_qs(parsed.query)

        assert "text" in query_params, "Call to API was missing 'text' query parameter"
        assert "buildings" in query_params["text"], "'buildings' was not in 'text' query parameter"

    @pytest.mark.vcr
    def test_fetch_dataset(self) -> None:
        dataset = Dataset.fetch('bigearthnet_v1')
        assert isinstance(dataset, Dataset)
        assert dataset.id == 'bigearthnet_v1'
        assert dataset.registry_url == 'https://mlhub.earth/bigearthnet_v1'
        assert dataset.doi == '10.14279/depositonce-10149'
        assert dataset.citation == "G. Sumbul, M. Charfuelan, B. Demir, V. Markl, " \
            "\"[BigEarthNet: A Large-Scale Benchmark Archive for Remote Sensing Image " \
            "Understanding](http://bigearth.net/static/documents/BigEarthNet_IGARSS_2019.pdf)\", " \
            "IEEE International Geoscience and Remote Sensing Symposium, pp. 5901-5904, Yokohama, Japan, 2019."

    @pytest.mark.vcr
    def test_get_dataset_by_doi(self):
        dataset_doi = "10.6084/m9.figshare.12047478.v2"
        ds = Dataset.fetch_by_doi(dataset_doi)
        assert ds.doi == dataset_doi

    @pytest.mark.vcr
    def test_get_dataset_by_id(self):
        dataset_id = 'ref_african_crops_kenya_02'
        ds = Dataset.fetch_by_id(dataset_id)
        assert ds.id == dataset_id

    @pytest.mark.dataset_id('ref_african_crops_kenya_02')
    def test_fetch_dataset_uses_id_when_appropriate(
            self,
            requests_mock: "Mocker_Type",
            root_url: str,
            stac_mock_json: str,
            ) -> None:
        """
        Uses request mocking to inspect the api request history.
        Uses stac_mock_json fixture to get mock api response.
        """
        dataset_id = "ref_african_crops_kenya_02"
        id_endpoint = urljoin(root_url, f"datasets/{dataset_id}")
        requests_mock.get(id_endpoint, status_code=200, text=stac_mock_json)

        Dataset.fetch(dataset_id)

        history = requests_mock.request_history
        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(id_endpoint).path

    @pytest.mark.dataset_id('ref_african_crops_kenya_02')
    def test_fetch_dataset_uses_doi_when_appropriate(
            self,
            requests_mock: "Mocker_Type",
            root_url: str,
            stac_mock_json: str,
            ) -> None:
        """
        Uses request mocking to inspect the api request history.
        Uses stac_mock_json fixture to get mock api response.
        """
        dataset_doi = "10.34911/rdnt.dw605x"
        doi_endpoint = urljoin(root_url, f"datasets/doi/{dataset_doi}")
        requests_mock.get(doi_endpoint, status_code=200, text=stac_mock_json)

        Dataset.fetch(dataset_doi)

        history = requests_mock.request_history
        assert len(history) == 1
        assert urlsplit(history[0].url).path == urlsplit(doi_endpoint).path

    def test_dataset_list_tags_filter(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        escaped_root_url = root_url.replace(".", r"\.")
        route_match = re.compile(f"^{escaped_root_url}datasets")
        requests_mock.get(route_match, status_code=200, text="[]")

        Dataset.list(tags=["segmentation", "sar"])

        history = requests_mock.request_history
        assert len(history) == 1

        parsed = urlsplit(history[0].url)
        query_params = parse_qs(parsed.query)

        assert "tags" in query_params, "Call to API was missing 'tags' query parameter"
        assert "segmentation" in query_params["tags"], "'segmentation' was not in 'tags' query parameter"
        assert "sar" in query_params["tags"], "'sar' was not in 'tags' query parameter"

    @pytest.mark.vcr
    def test_stac_catalog_size(self) -> None:
        expect_size = 263582
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        size = ds.stac_catalog_size()
        assert size is not None and size == expect_size, 'unexpected stac_catalog_size'

    @pytest.mark.vcr
    def test_estimated_dataset_size(self) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        size = ds.estimated_dataset_size()
        assert size is not None and size > 0, 'unexpected estimated_dataset_size'

    def checksum_asset_database(self, db: Path) -> str:
        with open(db, 'rb') as fh:
            return hashlib.md5(fh.read()).hexdigest()

    @pytest.mark.vcr
    def test_download_catalog_only(self, tmp_path: Path) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(output_dir=tmp_path, catalog_only=True)
        expect_archive_file = tmp_path / 'nasa_marine_debris.tar.gz'
        assert expect_archive_file.exists()
        stac_dir = tmp_path / 'nasa_marine_debris'
        expect_catalog_file = stac_dir / 'catalog.json'
        assert expect_catalog_file.exists()
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert not asset_db.exists()
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_all_assets_works(self, tmp_path: Path) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(output_dir=tmp_path)
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '45685e79f7ebc44cc7a8237301951b93'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_with_collection_filter_works(self, tmp_path: Path) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(
            output_dir=tmp_path,
            collection_filter=dict(nasa_marine_debris_labels=['labels'])
        )
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '0663697db11e3898935f5b5bd6e7a028'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_with_1_datetime_filter_works(self, tmp_path: Path) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(
            output_dir=tmp_path,
            datetime=parse("2018-12-15T00:00:00Z"),
        )
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '9b5b9e900596a58b6392907960e7796b'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_with_2_datetime_filter_works(self, tmp_path: Path) -> None:
        """
        download() with two datetime filter. (download not actually performed)
        """
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(
            output_dir=tmp_path,
            datetime=(parse("2018-12-15T00:00:00Z"), parse("2018-12-16T00:00:00Z")),
        )
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '912a226ae23f6a13a9d638b678a57fa6'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_with_bbox_filter_works(self, tmp_path: Path) -> None:
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(
            output_dir=tmp_path,
            bbox=[-87.5610, 5.9137, -87.5555, 15.9191],
        )
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '047eaec864a575c6e335dee5d300805d'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)

    @pytest.mark.vcr
    def test_download_with_intersects_filter_works(self, tmp_path: Path) -> None:
        nasa_marine_debris_aoi = json.loads(
            """
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [
                                -87.626953125,
                                15.961329081596643
                            ],
                            [
                                -87.626953125,
                                15.95604762305055
                            ],
                            [
                                -87.6214599609375,
                                15.95604762305055
                            ],
                            [
                                -87.6214599609375,
                                15.961329081596643
                            ],
                            [
                                -87.626953125,
                                15.961329081596643
                            ]
                        ]
                    ]
                }
            }
            """)
        ds = Dataset.fetch_by_id('nasa_marine_debris')
        ds.download(
            output_dir=tmp_path,
            intersects=nasa_marine_debris_aoi,
        )
        stac_dir = tmp_path / 'nasa_marine_debris'
        asset_db = stac_dir / 'mlhub_stac_assets.db'
        assert asset_db.exists()
        got_hash = self.checksum_asset_database(asset_db)
        expect_hash = '7e8852cb55fe6648ec1a80e85ad14800'
        assert got_hash == expect_hash
        rmtree(tmp_path, ignore_errors=True)


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
    def mock_profile(self, monkeypatch: pytest.MonkeyPatch, tmp_path: "Path_Type") -> Iterator[None]:
        """Overwrite the fixture in conftest so we don't set up an API key here"""

        # Monkeypatch the user's home directory to be the temp directory
        # This prevents the client from automatically finding any profiles configured in the user's
        # home directory.
        monkeypatch.setenv('HOME', str(tmp_path))  # Linux/Unix
        monkeypatch.setenv('USERPROFILE', str(tmp_path))  # Windows

        yield

    def test_fetch_with_api_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        """The Dataset class should use any API keys passed to Dataset.fetch in methods on the
        resulting Dataset instance."""
        dataset_id = cast(str, self.DATASET["id"])
        collection_id = self.COLLECTION["id"]
        api_key = 'test_api_key'

        dataset_url = urljoin(root_url, f'datasets/{dataset_id}')
        requests_mock.get(dataset_url, json=self.DATASET)

        collection_url = urljoin(root_url, f'collections/{collection_id}')
        requests_mock.get(collection_url, json=self.COLLECTION)

        dataset = Dataset.fetch(dataset_id, api_key=api_key)
        _ = dataset.collections

        history = requests_mock.request_history
        assert len(history) == 2
        assert f"key={api_key}" in history[1].url

    def test_list_with_api_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        """The Dataset class should use any API keys passed to Dataset.list in methods on the
        resulting dataset instances."""

        collection_id = self.COLLECTION["id"]
        api_key = 'test_api_key'

        dataset_url = urljoin(root_url, 'datasets')
        requests_mock.get(dataset_url, json=[self.DATASET])

        collection_url = urljoin(root_url, f'collections/{collection_id}')
        requests_mock.get(collection_url, json=self.COLLECTION)

        datasets = Dataset.list(api_key=api_key)
        for dataset in datasets:
            _ = dataset.collections

        history = requests_mock.request_history
        assert len(history) == 2
        assert f"key={api_key}" in history[1].url
