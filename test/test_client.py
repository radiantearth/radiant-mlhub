import radiant_mlhub.client


class TestClient:

    def test_list_collection_items(self, bigearthnet_v1_source_items):
        items = list(radiant_mlhub.client.list_collection_items('bigearthnet_v1_source', limit=40))

        assert len(items) == 40
        assert 'assets' in items[0]
        assert items[0]['id'] == 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'

    def test_get_collection_item(self, bigearthnet_v1_source_item):
        item = radiant_mlhub.client.get_collection_item(
            'bigearthnet_v1_source',
            'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'
        )

        assert item['stac_extensions'] == ['eo']
        assert item['id'] == 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62'
