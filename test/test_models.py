import configparser

import pystac
import pytest
from radiant_mlhub.models import Collection


class TestCollection:

    @pytest.fixture(autouse=True)
    def mock_profile(self, monkeypatch, tmp_path):
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

    def test_list_collections(self, collections_list):
        collections = list(Collection.list())
        assert len(collections) == 47
        assert isinstance(collections[0], Collection)

    def test_get_collection_from_file(self, bigearthnet_v1_source):
        """The collection can be fetched by passing the MLHub URL to the from_file method."""
        collection = Collection.from_file(bigearthnet_v1_source)

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_get_collection_from_mlhub(self, bigearthnet_v1_source):
        collection = Collection.from_mlhub('bigearthnet_v1_source')

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_get_items(self, bigearthnet_v1_source, bigearthnet_v1_source_items):
        """Collection items can be fetched using the overridden get_items method."""
        collection = Collection.from_file(bigearthnet_v1_source)

        items = list(collection.get_items())

        assert len(items) == 60
        assert items[0].id != items[30].id  # Check that the pages contain new items
        assert isinstance(items[0], pystac.Item)
