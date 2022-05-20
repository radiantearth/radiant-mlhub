import json
from typing import TYPE_CHECKING, Any, Dict
from urllib.parse import parse_qs, urljoin, urlsplit
from pathlib import Path
import pystac.item
import pytest
from radiant_mlhub.models import Collection
from radiant_mlhub.session import ANONYMOUS_PROFILE


if TYPE_CHECKING:
    from pathlib import Path as Path_Type

    from requests_mock import Mocker as Mocker_Type


@pytest.fixture(autouse=False)
def stac_mock_json(request) -> str:
    """
    Reads a mocked api response from data/**/*.json files.
    """
    collection_mark = request.node.get_closest_marker('collection_id')
    print(collection_mark)
    mock_data_dir = Path(__file__).parent.parent / 'data'
    if collection_mark is not None:
        (collection_id, ) = collection_mark.args
        response_path = mock_data_dir / 'collections' / f'{collection_id}.json'
    else:
        pytest.fail('pytest fixture test_collection.stac_mock_json is misconfigured.')
    with response_path.open(encoding='utf-8') as src:
        return src.read()


class TestCollection:

    @pytest.mark.vcr
    def test_dunder_str_method(self) -> None:
        collection_id = 'bigearthnet_v1_source'
        collection = Collection.fetch(collection_id)
        expect_str = 'bigearthnet_v1_source: BigEarthNet v1.0'
        got_str = str(collection)
        assert got_str == expect_str

    @pytest.mark.vcr
    def test_list_collections(self) -> None:
        collections = Collection.list()
        assert isinstance(collections, list)
        assert isinstance(collections[0], Collection)

    @pytest.mark.vcr
    def test_fetch_collection(self) -> None:
        collection = Collection.fetch('bigearthnet_v1_source')

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    @pytest.mark.vcr
    def test_get_items_error(self) -> None:
        collection = Collection.fetch('bigearthnet_v1_source')

        with pytest.raises(NotImplementedError) as excinfo:
            collection.get_items()

        assert 'For performance reasons, the get_items method has not been implemented for Collection instances. Please ' \
               'use the Dataset.download method to download Dataset assets.' == str(excinfo.value)

    @pytest.mark.vcr
    def test_get_registry_url(self) -> None:
        collection = Collection.fetch('ref_african_crops_kenya_02_labels')
        assert collection.registry_url == 'https://mlhub.earth/10.34911/rdnt.dw605x'

    @pytest.mark.vcr
    def test_get_registry_url_no_doi(self) -> None:
        # Get the example collection as a dict and remove the sci:doi property
        collection_dict: Dict[str, Any] = Collection.fetch('ref_african_crops_kenya_02_labels').to_dict()
        collection_dict.pop('sci:doi', None)
        collection: Collection = Collection.from_dict(collection_dict)

        assert collection.registry_url is None

    @pytest.mark.vcr
    def test_get_archive_size(self) -> None:
        collection = Collection.fetch('bigearthnet_v1_labels')
        assert collection.archive_size == 173029030


class TestCollectionAuthenticatedEndpoints:

    @pytest.mark.vcr
    def test_fetch_item(self) -> None:
        collection = Collection.fetch('ref_african_crops_kenya_02_source')
        item = collection.fetch_item('ref_african_crops_kenya_02_tile_02_20190721')

        assert isinstance(item, pystac.item.Item)
        assert len(item.assets) == 13

    @pytest.mark.vcr
    def test_download_archive(self, tmp_path: "Path_Type") -> None:
        collection = Collection.fetch('ref_african_crops_kenya_02_labels')
        output_path = collection.download(output_dir=tmp_path)

        assert output_path == tmp_path / 'ref_african_crops_kenya_02_labels.tar.gz'
        assert output_path.exists()


class TestAnonymousCollection:

    @pytest.fixture(autouse=True)
    def mock_profile(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # remove this (all these) env var otherwise it will override the anonymous profile.
        monkeypatch.delenv('MLHUB_API_KEY', raising=False)
        monkeypatch.delenv(' MLHUB_PROFILE', raising=False)

    def test_list_anonymously_has_no_key(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        url = urljoin(root_url, 'collections')

        # Don't really care about the response here, since we're just interested in the request
        # parameters. We test that this gives a valid response in a different test
        requests_mock.get(url, json={"collections": []})

        _ = Collection.list(profile=ANONYMOUS_PROFILE)

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.collection_id('bigearthnet_v1_source')
    def test_fetch_anonymously_has_no_key(
                self,
                requests_mock: "Mocker_Type",
                root_url: str,
                stac_mock_json: str,
            ) -> None:
        collection_id = 'bigearthnet_v1_source'
        url = urljoin(root_url, f'collections/{collection_id}')
        requests_mock.get(url, json=json.loads(stac_mock_json))

        _ = Collection.fetch(collection_id, profile=ANONYMOUS_PROFILE)

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs

    @pytest.mark.collection_id('bigearthnet_v1_source')
    def test_fetch_passes_session_to_instance(
                self,
                requests_mock: "Mocker_Type",
                root_url: str,
                stac_mock_json: str
            ) -> None:
        collection_id = 'bigearthnet_v1_source'
        collection_url = urljoin(root_url, f'collections/{collection_id}')

        requests_mock.get(collection_url, json=json.loads(stac_mock_json))

        collection = Collection.fetch(collection_id, profile=ANONYMOUS_PROFILE)
        assert collection.session_kwargs.get("profile") == ANONYMOUS_PROFILE

    @pytest.mark.collection_id('bigearthnet_v1_source')
    def test_anonymous_archive_size(
            self,
            requests_mock: "Mocker_Type",
            root_url: str,
            stac_mock_json: str,
            ) -> None:
        collection_id = 'bigearthnet_v1_source'
        collection = Collection.from_dict(
            json.loads(stac_mock_json), profile=ANONYMOUS_PROFILE
        )
        info_url = urljoin(root_url, f'archive/{collection_id}/info')
        requests_mock.get(info_url, json={})

        _ = collection.archive_size

        history = requests_mock.request_history

        actual_url = history[0].url
        qs = parse_qs(urlsplit(actual_url).query)
        assert "key" not in qs
