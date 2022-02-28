"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from __future__ import annotations

from datetime import datetime as Datetime
from typing import Any, Dict, List, Optional, Union, cast

from pystac.catalog import Catalog
from pystac.collection import Collection
from pystac.item import Item

from .. import client


class MLModel(Item):

    session_kwargs: Dict[str, Any] = {}

    """
    Class inheriting from :class:`pystac.Item` that adds some convenience methods for listing and fetching from the Radiant MLHub API.
    """
    def __init__(
        self,
        id: str,
        geometry: Optional[Dict[str, Any]],
        bbox: Optional[List[float]],
        datetime: Optional[Datetime],
        properties: Dict[str, Any],
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        collection: Optional[Union[str, Collection]] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        *,
        api_key: Optional[str] = None,
        profile: Optional[str] = None
    ):
        super().__init__(
            id=id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime,
            properties=properties,
            stac_extensions=stac_extensions,
            href=href,
            collection=collection,
            extra_fields=extra_fields,
        )
        self.session_kwargs = {}
        if api_key is not None:
            self.session_kwargs['api_key'] = api_key
        if profile is not None:
            self.session_kwargs['profile'] = profile

    @classmethod
    def fetch(cls, model_id: str,  *, api_key: Optional[str] = None, profile: Optional[str] = None) -> MLModel:
        """Fetches a :class:`MLModel` instance by id.

        Parameters
        ----------
        model_id : str
            The ID of the ML Model to fetch (e.g. ``model-cyclone-wind-estimation-torchgeo-v1``).
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        model : MLModel
        """
        d = client.get_model_by_id(model_id, api_key=api_key, profile=profile)
        return cls.from_dict(d, api_key=api_key, profile=profile)

    @classmethod
    def list(cls, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> List[MLModel]:
        """Returns a list of :class:`MLModel` instances for all models hosted by MLHub.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        ------
        models : List[MLModel]
        """
        return [
            cls.from_dict(ml_model)
            for ml_model in client.list_models(api_key=api_key, profile=profile)
        ]

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
        *,
        api_key: Optional[str] = None,
        profile: Optional[str] = None
    ) -> MLModel:
        """Patches the :meth:`pystac.Item.from_dict` method so that it returns the calling
        class instead of always returning a :class:`pystac.Item` instance."""
        item = super().from_dict(d)
        ml_model = cast(MLModel, item)
        ml_model.session_kwargs = {}
        if api_key is not None:
            ml_model.session_kwargs['api_key'] = api_key
        if profile is not None:
            ml_model.session_kwargs['profile'] = profile
        return ml_model
