import os

import pytest
import pystac
from radiant_mlhub.models import Collection


class TestCollection:

    @pytest.fixture(autouse=True)
    def mock_api_key(self, monkeypatch):
        """Set the default (dummy) API key to use for testing."""
        monkeypatch.setenv('MLHUB_API_KEY', 'testapikey')
        return os.getenv('MLHUB_API_KEY')

    def test_list_collections(self, collections_list):
        collections = Collection.list()
        assert len(collections) == 47
        assert isinstance(collections[0], Collection)

    def test_get_collection_from_file(self, bigearthnet_v1_source):
        """The collection can be fetched by passing the MLHub URL to the from_file method."""
        collection = Collection.from_file(bigearthnet_v1_source)

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_get_collection_from_mlhub(self, bigearthnet_v1_source):
        collection = Collection.fetch('bigearthnet_v1_source')

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_get_items_error(self, bigearthnet_v1_source):
        collection = Collection.fetch('bigearthnet_v1_source')

        with pytest.raises(NotImplementedError) as excinfo:
            collection.get_items()

        assert 'For performance reasons, the get_items method has not been implemented for Collection instances.' == str(excinfo.value)

    def test_fetch_item(self, bigearthnet_v1_source, bigearthnet_v1_source_item):
        collection = Collection.fetch('bigearthnet_v1_source')
        item = collection.fetch_item('bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62')

        assert isinstance(item, pystac.Item)
        assert len(item.assets) == 13
