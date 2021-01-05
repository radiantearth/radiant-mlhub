import pytest
import radiant_mlhub.client
from radiant_mlhub.exceptions import MLHubException, CollectionDoesNotExist


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

    @pytest.fixture
    def collection_does_not_exist(self, requests_mock):
        endpoint = 'https://api.radiant.earth/mlhub/v1/collections/does_not_exist'

        requests_mock.get(
            endpoint,
            status_code=404,
            reason='NOT FOUND',
            headers={'Content-Type': 'text/html; charset=utf-8'},
            text='<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
                 '<title>404 Not Found</title>\n<h1>Not Found</h1>\n'
                 '<p>The requested URL was not found on the server. '
                 'If you entered the URL manually please check your spelling and try again.</p>\n'
        )

        yield endpoint

    @pytest.fixture
    def internal_server_error(self, requests_mock):
        endpoint = 'https://api.radiant.earth/mlhub/v1/collections/internal_error'

        requests_mock.get(
            endpoint,
            status_code=500,
            reason='Internal Server Error',
            headers={'Content-Type': 'text/html; charset=utf-8'},
            text='<html>\n  <head>\n    <title>Internal Server Error</title>\n  '
                 '</head>\n  <body>\n    <h1><p>Internal Server Error</p></h1>\n    \n  </body>\n</html>\n'
        )

        yield endpoint

    def test_collection_does_not_exist(self, collection_does_not_exist):
        with pytest.raises(CollectionDoesNotExist) as excinfo:
            radiant_mlhub.client.get_collection('does_not_exist')

        assert 'Collection "does_not_exist" does not exist' in str(excinfo.value)

    def test_internal_server_error(self, internal_server_error):
        with pytest.raises(MLHubException) as excinfo:
            radiant_mlhub.client.get_collection('internal_error')

        assert 'Internal Server Error' in str(excinfo.value)
