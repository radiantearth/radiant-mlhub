from typing import TYPE_CHECKING

import pytest
from pystac.asset import Asset
from pystac.link import Link
from radiant_mlhub.models import MLModel


if TYPE_CHECKING:
    from requests_mock import Mocker as Mocker_Type


class TestMLModel:

    @pytest.mark.vcr
    def test_list_ml_models(self) -> None:
        """MLModel.list returns a list of MLModel instances."""
        ml_models = MLModel.list()
        assert isinstance(ml_models[0], MLModel)

    @pytest.mark.vcr
    def test_fetch_ml_model_by_id(self) -> None:
        expect_id = 'model-cyclone-wind-estimation-torchgeo-v1'
        ml_model = MLModel.fetch(expect_id)
        assert isinstance(ml_model, MLModel)
        assert ml_model.id == expect_id
        assert len(ml_model.links) > 0
        assert len(ml_model.bbox) > 0
        assert ml_model.collection_id == 'model-cyclone-wind-estimation-torchgeo'
        assert ml_model.properties.get('title') == 'Tropical Cyclone Wind Estimation Model'
        assert ml_model.properties.get('sci:doi') == '10.5281/zenodo.5773331'
        assert ml_model.properties.get('ml-model:type') == 'ml-model'
        assert len(ml_model.properties.get('providers'))
        assert len(ml_model.properties.get('sci:publications'))
        assert isinstance(ml_model.assets.get('inferencing-compose'), Asset)
        assert isinstance(ml_model.assets.get('inferencing-checkpoint'), Asset)
        assert len(ml_model.links) > 0
        assert isinstance(ml_model.links[0], Link)

    @pytest.mark.vcr
    def test_ml_model_resolves_links(self) -> None:
        expect_id = 'model-cyclone-wind-estimation-torchgeo-v1'
        ml_model = MLModel.fetch(expect_id)
        for link in ml_model.links:
            assert isinstance(link, Link)
            assert link.href is not None

    @pytest.mark.skip(reason="MLModel get by doi is not implemented")
    def test_get_ml_model_by_doi(self, requests_mock: "Mocker_Type", root_url: str) -> None:
        pass

    @pytest.mark.vcr
    def test_dunder_str_method(self) -> None:
        model_id = 'model-cyclone-wind-estimation-torchgeo-v1'
        ml_model = MLModel.fetch(model_id)
        expect_str = 'model-cyclone-wind-estimation-torchgeo-v1: Tropical Cyclone Wind Estimation Model'  # noqa: E501
        got_str = str(ml_model)
        assert got_str == expect_str
