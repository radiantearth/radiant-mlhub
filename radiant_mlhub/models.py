"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from copy import deepcopy
from typing import Iterator, List, Optional
import concurrent.futures
from enum import Enum
from collections.abc import Sequence

try:
    from functools import cached_property  # type: ignore [attr-defined]
except ImportError:  # pragma: no cover
    from backports.cached_property import cached_property  # type: ignore [no-redef]


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
        """Creates a :class:`Collection` instance by fetching the collection with the given ID from the Radiant MLHub API.

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


class CollectionType(Enum):
    """Valid values for the type of a collection associated with a Radiant MLHub dataset."""
    SOURCE = 'source_imagery'
    LABELS = 'labels'


class _CollectionWithType:
    def __init__(self, collection: Collection, types: List[str]):
        self.types = [CollectionType(type_) for type_ in types]
        self.collection = collection


class _CollectionList(Sequence):
    """Used internally by :class:`Dataset` to create a list of collections that can also be accessed by type using the
    ``source_imagery`` and ``labels`` attributes."""

    def __init__(self, collections_with_type: List[_CollectionWithType]):
        self._collections = collections_with_type

    def __iter__(self):
        for item in self._collections:
            yield item.collection

    def __len__(self):
        return len(self._collections)

    def __getitem__(self, item):
        return self._collections[item].collection

    def __repr__(self):
        return list(self.__iter__()).__repr__()

    @cached_property
    def source_imagery(self):
        return [
            c.collection
            for c in self._collections
            if any(type_ is CollectionType.SOURCE for type_ in c.types)
        ]

    @cached_property
    def labels(self):
        return [
            c.collection
            for c in self._collections
            if any(type_ is CollectionType.LABELS for type_ in c.types)
        ]


class Dataset:
    """Class that brings together multiple Radiant MLHub "collections" that are all considered part of a single "dataset". For instance,
    the ``bigearthnet_v1`` dataset is composed of both a source imagery collection (``bigearthnet_v1_source``) and a labels collection
    (``bigearthnet_v1_labels``).
    """

    def __init__(self, id: str, collections: List[dict], title: Optional[str] = None, **session_kwargs):
        self.id = id
        self.title = title
        self.collection_descriptions = collections
        self.session_kwargs = session_kwargs

    @cached_property
    def collections(self) -> _CollectionList:
        """List of collections associated with this dataset. The list that is returned has 2 additional attributes (``source_imagery`` and
        ``labels``) that represent the list of collections corresponding the each type.

        .. note::

            This is a cached property, so updating ``self.collection_descriptions`` after calling ``self.collections`` the first time
            will have no effect on the results. See :func:`functools.cached_property` for details on clearing the cached value.

        Examples
        --------

        >>> from radiant_mlhub import Dataset
        >>> dataset = Dataset.fetch('bigearthnet_v1')
        >>> len(dataset.collections)
        2
        >>> len(dataset.collections.source_imagery)
        1
        >>> len(dataset.collections.labels)
        1

        To loop through all collections

            >>> for collection in dataset.collections:
            ...     # Do something here

        To loop through only the source imagery collections:

            >>> for collection in dataset.collections.source_imagery:
            ...     # Do something here

        To loop through only the label collections:

            >>> for collection in dataset.collections.labels:
            ...     # Do something here
        """
        # Internal method to return a Collection along with it's CollectionType
        def _fetch_collection(_collection_description):
            return _CollectionWithType(
                Collection.fetch(_collection_description['id'], **self.session_kwargs),
                [CollectionType(type_) for type_ in _collection_description['types']]
            )

        # Fetch all collections and create Collection instances
        if len(self.collection_descriptions) == 1:
            # If there is only 1 collection, fetch it in the same thread
            only_description = self.collection_descriptions[0]
            collections = [_fetch_collection(only_description)]
        else:
            # If there are multiple collections, fetch them concurrently
            with concurrent.futures.ThreadPoolExecutor() as exc:
                collections = list(exc.map(_fetch_collection, self.collection_descriptions))

        return _CollectionList(collections)

    @classmethod
    def list(cls, **session_kwargs) -> Iterator['Dataset']:
        """Yields :class:`Dataset` instances for all datasets hosted by MLHub.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        **session_kwargs
            Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`

        Yields
        ------
        dataset : Dataset
        """
        yield from map(lambda d: cls(**d), client.list_datasets(**session_kwargs))

    @classmethod
    def fetch(cls, dataset_id: str, **session_kwargs) -> 'Dataset':
        """Creates a :class:`Dataset` instance by fetching the dataset with the given ID from the Radiant MLHub API.

        Parameters
        ----------
        dataset_id : str
            The ID of the dataset to fetch (e.g. ``bigearthnet_v1``).
        **session_kwargs
            Keyword arguments passed directly to :func:`~radiant_mlhub.session.get_session`.

        Returns
        -------
        dataset : Dataset
        """
        return cls(**client.get_dataset(dataset_id, **session_kwargs))
