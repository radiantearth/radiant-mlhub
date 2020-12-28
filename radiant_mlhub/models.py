from copy import deepcopy
from typing import Optional, Iterator

import pystac

from .session import get_session


class Collection(pystac.Collection):
    """Sub-class of :class:`pystac.Collection` that overrides the :meth:`pystac.Catalog.get_items` to fetch item links from the
    ``collections/<collection_id>/items`` MLHub endpoint instead of trying to use static links within the catalog object.
    """

    @classmethod
    def list(cls, api_key: Optional[str] = None, profile: Optional[str] = None) -> Iterator['Collection']:
        """Yields :class:`Collection` instances for all collections hosted by MLHub.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        api_key : str, optional
            An API key to use for the requests.
        profile: str, optional
            A named profile from ``~/.mlhub/profiles`` to use for the request.

        Yields
        ------
        collection : Collection
        """
        session = get_session(api_key=api_key, profile=profile)
        for page in session.paginate('collections'):
            for _collection in page.get('collections', []):
                yield cls.from_dict(_collection)

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
    def from_mlhub(cls, collection_id: str) -> 'Collection':
        """Creates a :class:`Collection` instance by fetching the collection with the given ID from MLHub.

        Parameters
        ----------
        collection_id : str
            The ID of the collection to fetch (e.g. ``bigearthnet_v1_source``).

        Returns
        -------
        collection : Collection
        """
        session = get_session()
        response = session.get(f'collections/{collection_id}').json()
        return cls.from_dict(response)

    def get_items(self, api_key: Optional[str] = None, profile: Optional[str] = None) -> Iterator[pystac.Item]:
        """Overrides the :meth:`pystac.Catalog.get_items` method to fetch items using the ``collections/<collection_id>/items`` endpoint
        instead of looking for static links within the ``Collection`` object.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        api_key : str, optional
            An API key to use for the requests.
        profile: str, optional
            A named profile from ``~/.mlhub/profiles`` to use for the request.
        Yields
        ------
        item : pystac.Item
        """
        session = get_session(api_key=api_key, profile=profile)
        for page in session.paginate(f'collections/{self.id}/items'):
            for feature in page.get('features', []):
                yield pystac.Item.from_dict(feature)
