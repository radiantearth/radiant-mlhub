import pytest
import pystac
from radiant_mlhub.models import Collection, Dataset


class TestCollection:

    def test_list_collections(self, collections):
        collections = Collection.list()
        assert len(collections) == 47
        assert isinstance(collections[0], Collection)

    def test_get_collection_from_file(self, source_collection):
        """The collection can be fetched by passing the MLHub URL to the from_file method."""
        collection = Collection.from_file(source_collection)

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_fetch_collection(self, source_collection):
        collection = Collection.fetch('bigearthnet_v1_source')

        assert isinstance(collection, Collection)
        assert collection.description == 'BigEarthNet v1.0'

    def test_get_items_error(self, source_collection):
        collection = Collection.fetch('bigearthnet_v1_source')

        with pytest.raises(NotImplementedError) as excinfo:
            collection.get_items()

        assert 'For performance reasons, the get_items method has not been implemented for Collection instances. Please ' \
               'use the Collection.download method to download Collection assets.' == str(excinfo.value)

    def test_fetch_item(self, source_collection, source_collection_item):
        collection = Collection.fetch('bigearthnet_v1_source')
        item = collection.fetch_item('bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62')

        assert isinstance(item, pystac.Item)
        assert len(item.assets) == 13

    def test_download_archive(self, source_collection_archive, source_collection, tmp_path):
        collection = Collection.fetch('bigearthnet_v1_source')
        output_path = collection.download(output_dir=tmp_path)

        assert output_path == tmp_path / 'bigearthnet_v1_source.tar.gz'
        assert output_path.exists()


class TestDataset:

    def test_list_datasets(self, datasets):
        """Dataset.list returns a list of Dataset instances."""
        datasets = list(Dataset.list())
        assert len(datasets) == 19
        assert isinstance(datasets[0], Dataset)

    def test_fetch_dataset(self, dataset):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert isinstance(dataset, Dataset)
        assert dataset.id == 'bigearthnet_v1'

    def test_dataset_collections(self, dataset, source_collection, labels_collection):
        dataset = Dataset.fetch('bigearthnet_v1')
        assert len(dataset.collections) == 2
        assert len(dataset.collections.source_imagery) == 1
        assert len(dataset.collections.labels) == 1
        assert all(isinstance(c, Collection) for c in dataset.collections)
        assert dataset.collections[0] in dataset.collections.source_imagery

    def test_download_collection_archives(
            self,
            dataset,
            source_collection,
            labels_collection,
            source_collection_archive,
            labels_collection_archive,
            tmp_path,
    ):
        dataset = Dataset.fetch('bigearthnet_v1')
        output_paths = dataset.download(output_dir=tmp_path)

        assert all(p.exists() for p in output_paths)

    def test_collections_list(self, dataset, source_collection, labels_collection):
        dataset_ = Dataset.fetch(dataset)
        assert dataset_.collections.__repr__() == '[<Collection id=bigearthnet_v1_source>, <Collection id=bigearthnet_v1_labels>]'
