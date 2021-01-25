"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from copy import deepcopy
from typing import Iterator, List

import pystac

from . import client


class Collection(pystac.Collection):
    """Class inheriting from :class:`pystac.Collection` that overrides the :meth:`pystac.Catalog.get_items` to fetch item links from the
    ``collections/<collection_id>/items`` MLHub endpoint instead of trying to use static links within the catalog object.
    """

    @classmethod
    def list(cls, **session_kwargs) -> List['Collection']:
        """Returns a list of :class:`Collection` instances for all collections hosted by MLHub.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        **session_kwargs
            Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

        Returns
        ------
        collections : List[Collection]
        """
        return [
            cls.from_dict(collection)
            for collection in client.list_collections(**session_kwargs)
        ]

    @classmethod
    def from_dict(cls, d, href=None, root=None):
        """Patches the :meth:`pystac.Collection.from_dict` method so that it returns the calling class instead of always returning
        a :class:`pystac.Collection` instance."""
        catalog_type = pystac.CatalogType.determine_type(d)

        d = deepcopy(d)
        id_ = d.pop('id')
        description = d.pop('description')
        license_ = d.pop('license')
        extent = pystac.Extent.from_dict(d.pop('extent'))
        title = d.get('title')
        stac_extensions = d.get('stac_extensions')
        keywords = d.get('keywords')
        providers = d.get('providers')
        if providers is not None:
            providers = list(map(lambda x: pystac.Provider.from_dict(x), providers))
        properties = d.get('properties')
        summaries = d.get('summaries')
        links = d.pop('links')

        d.pop('stac_version')

        collection = cls(
            id=id_,
            description=description,
            extent=extent,
            title=title,
            stac_extensions=stac_extensions,
            extra_fields=d,
            license=license_,
            keywords=keywords,
            providers=providers,
            properties=properties,
            summaries=summaries,
            href=href,
            catalog_type=catalog_type
        )

        for link in links:
            if link['rel'] == 'root':
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links('root')

            if link['rel'] != 'self' or href is None:
                collection.add_link(pystac.Link.from_dict(link))

        return collection

    @classmethod
    def fetch(cls, collection_id: str, **session_kwargs) -> 'Collection':
        """Creates a :class:`Collection` instance by fetching the collection with the given ID from MLHub.

        Parameters
        ----------
        collection_id : str
            The ID of the collection to fetch (e.g. ``bigearthnet_v1_source``).
        **session_kwargs
            Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

        Returns
        -------
        collection : Collection
        """
        response = client.get_collection(collection_id, **session_kwargs)
        return cls.from_dict(response)

    def get_items(self, **session_kwargs) -> Iterator[pystac.Item]:
        """
        .. note::

            The ``get_items`` method is not implemented for Radiant MLHub :class:`Collection` instances for performance reasons.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError('For performance reasons, the get_items method has not been implemented for Collection instances.')

    def fetch_item(self, item_id: str, **session_kwargs) -> pystac.Item:
        response = client.get_collection_item(self.id, item_id)
        return pystac.Item.from_dict(response)
