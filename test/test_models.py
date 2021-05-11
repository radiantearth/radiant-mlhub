import pystac
import pytest

from radiant_mlhub.models import Collection, Dataset


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


class TestDataset:

    @pytest.mark.vcr
    def test_list_datasets(self):
        """Dataset.list returns a list of Dataset instances."""
        datasets = list(Dataset.list())
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
