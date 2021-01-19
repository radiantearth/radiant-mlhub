import pytest
import pystac
from radiant_mlhub.models import Collection, Dataset


class TestCollection:

    def test_list_collections(self, collections_list):
        collections = Collection.list()
        assert len(collections) == 47
        assert isinstance(collections[0], Collection)

    def test_get_collection_from_file(self, bigearthnet_v1_source):
        """The collection can be fetched by passing the MLHub URL to the from_file method."""
        collection = Collection.from_file(bigearthnet_v1_source)

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_fetch_collection(self, bigearthnet_v1_source):
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

    @pytest.mark.skip('Needs update for concurrent downloads')
    def test_download_archive(self, collection_archive, bigearthnet_v1_source, tmp_path):
        collection = Collection.fetch('bigearthnet_v1_source')
        collection.download(output_path=tmp_path / 'download.tar.gz')

        assert (tmp_path / 'download.tar.gz').exists()


class TestDataset:

    def test_list_datasets(self, datasets_list):
        """Dataset.list returns a list of Dataset instances."""
        datasets = list(Dataset.list())
        assert len(datasets) == 19
        assert isinstance(datasets[0], Dataset)

    def test_fetch_dataset(self, bigearthnet_v1_dataset):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert isinstance(dataset, Dataset)
        assert dataset.id == 'bigearthnet_v1'

    def test_dataset_collections(self, bigearthnet_v1_dataset, bigearthnet_v1_source, bigearthnet_v1_labels):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert len(dataset.collections) == 2
        assert len(dataset.collections.source_imagery) == 1
        assert len(dataset.collections.labels) == 1
        assert all(isinstance(c, Collection) for c in dataset.collections)
        assert dataset.collections[0] in dataset.collections.source_imagery
