"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from __future__ import annotations

import concurrent.futures
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union

from .. import client
from . import Collection

TagOrTagList = Union[str, Iterable[str]]
TextOrTextList = Union[str, Iterable[str]]


class Dataset:
    """Class that brings together multiple Radiant MLHub "collections" that are all considered part of a single "dataset". For instance,
    the ``bigearthnet_v1`` dataset is composed of both a source imagery collection (``bigearthnet_v1_source``) and a labels collection
    (``bigearthnet_v1_labels``).

    Attributes
    ----------

    id : str
        The dataset ID.
    title : str or None
        The title of the dataset (or ``None`` if dataset has no title).
    registry_url : str or None
        The URL to the registry page for this dataset, or ``None`` if no registry page exists.
    doi : str or None
        The DOI identifier for this dataset, or ``None`` if there is no DOI for this dataset.
    citation: str or None
        The citation information for this dataset, or ``None`` if there is no citation information.
    """

    def __init__(
        self,
        id: str,
        collections: List[Dict[str, Any]],
        title: Optional[str] = None,
        registry: Optional[str] = None,
        doi: Optional[str] = None,
        citation: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
        profile: Optional[str] = None,
        # Absorbs additional keyword arguments to protect against changes to dataset object from API
        # https://github.com/radiantearth/radiant-mlhub/issues/41
        **_: Any
    ):
        self.id = id
        self.title = title
        self.collection_descriptions = collections
        self.registry_url = registry
        self.doi = doi
        self.citation = citation

        self.session_kwargs = {}
        if api_key:
            self.session_kwargs['api_key'] = api_key
        if profile:
            self.session_kwargs['profile'] = profile

        self._collections: Optional['_CollectionList'] = None

    @property
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
        if self._collections is None:
            # Internal method to return a Collection along with it's CollectionType
            def _fetch_collection(_collection_description: Dict[str, Any]) -> _CollectionWithType:
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

            self._collections = _CollectionList(collections)

        return self._collections

    @classmethod
    def list(
        cls,
        *,
        tags: Optional[TagOrTagList] = None,
        text: Optional[TextOrTextList] = None,
        api_key: Optional[str] = None,
        profile: Optional[str] = None
    ) -> List['Dataset']:
        """Returns a list of :class:`Dataset` instances for each datasets hosted by MLHub.

        See the :ref:`Authentication` documentation for details on how authentication is handled for this request.

        Parameters
        ----------
        tags : A list of tags to filter datasets by. If not ``None``, only datasets containing all
            provided tags will be returned.
        text : A list of text phrases to filter datasets by. If not ``None``, only datasets
            containing all phrases will be returned.
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Yields
        ------
        dataset : Dataset
        """
        return [
            cls(**d, api_key=api_key, profile=profile)
            for d in client.list_datasets(tags=tags, text=text, api_key=api_key, profile=profile)
        ]

    @classmethod
    def fetch_by_doi(cls, dataset_doi: str, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> "Dataset":
        """Creates a :class:`Dataset` instance by fetching the dataset with the given DOI from the Radiant MLHub API.

        Parameters
        ----------
        dataset_doi : str
            The DOI of the dataset to fetch (e.g. ``10.6084/m9.figshare.12047478.v2``).
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        dataset : Dataset
        """
        return cls(
            **client.get_dataset_by_doi(dataset_doi, api_key=api_key, profile=profile),
            api_key=api_key,
            profile=profile,
        )

    @classmethod
    def fetch_by_id(cls, dataset_id: str,  *, api_key: Optional[str] = None, profile: Optional[str] = None) -> 'Dataset':
        """Creates a :class:`Dataset` instance by fetching the dataset with the given ID from the Radiant MLHub API.

        Parameters
        ----------
        dataset_id : str
            The ID of the dataset to fetch (e.g. ``bigearthnet_v1``).
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        dataset : Dataset
        """
        return cls(
            **client.get_dataset_by_id(
                dataset_id,
                api_key=api_key,
                profile=profile
            )
        )

    @classmethod
    def fetch(cls, dataset_id_or_doi: str,  *, api_key: Optional[str] = None, profile: Optional[str] = None) -> 'Dataset':
        """Creates a :class:`Dataset` instance by first trying to fetching the dataset based on ID,
        then falling back to fetching by DOI.

        Parameters
        ----------
        dataset_id_or_doi : str
            The ID or DOI of the dataset to fetch (e.g. ``bigearthnet_v1``).
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        dataset : Dataset
        """
        return cls(
            **client.get_dataset(dataset_id_or_doi, api_key=api_key, profile=profile),
            api_key=api_key,
            profile=profile,
        )

    def download(
            self,
            output_dir: Union[Path, str],
            *,
            if_exists: str = 'resume',
            api_key: Optional[str] = None,
            profile: Optional[str] = None
    ) -> List[Path]:
        """Downloads archives for all collections associated with this dataset to given directory. Each archive will be named using the
        collection ID (e.g. some_collection.tar.gz). If ``output_dir`` does not exist, it will be created.

        .. note::

            Some collections may be very large and take a significant amount of time to download, depending on your connection speed.

        Parameters
        ----------
        output_dir : str or pathlib.Path
            The directory into which the archives will be written.
        if_exists : str, optional
            How to handle an existing archive at the same location. If ``"skip"``, the download will be skipped. If ``"overwrite"``,
            the existing file will be overwritten and the entire file will be re-downloaded. If ``"resume"`` (the default), the
            existing file size will be compared to the size of the download (using the ``Content-Length`` header). If the existing
            file is smaller, then only the remaining portion will be downloaded. Otherwise, the download will be skipped.
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        output_paths : List[pathlib.Path]
            List of paths to the downloaded archives

        Raises
        -------
        IOError
            If ``output_dir`` exists and is not a directory.
        FileExistsError
            If one of the archive files already exists in the ``output_dir`` and both ``exist_okay`` and ``overwrite`` are ``False``.
        """
        return [
            collection.download(output_dir, if_exists=if_exists, api_key=api_key, profile=profile)
            for collection in self.collections
        ]

    @property
    def total_archive_size(self) -> Optional[int]:
        """Gets the total size (in bytes) of the archives for all collections associated with this
        dataset. If no archives exist, returns ``None``."""
        # Since self.collections is cached on the Dataset instance, and collection.archive_size is
        # cached on each Collection, we don't bother to cache this property.
        archive_sizes = [
            collection.archive_size
            for collection in self.collections
            if collection.archive_size is not None
        ]

        return None if not archive_sizes else sum(archive_sizes)


class CollectionType(Enum):
    """Valid values for the type of a collection associated with a Radiant MLHub dataset."""
    SOURCE = 'source_imagery'
    LABELS = 'labels'


class _CollectionWithType:
    def __init__(self, collection: Collection, types: List[CollectionType]):
        self.types = [CollectionType(type_) for type_ in types]
        self.collection = collection


class _CollectionList:
    """Used internally by :class:`Dataset` to create a list of collections that can also be accessed by type using the
    ``source_imagery`` and ``labels`` attributes."""
    _source_imagery: Optional[List[Collection]]
    _labels: Optional[List[Collection]]
    _collections: List[_CollectionWithType]

    def __init__(self, collections_with_type: List[_CollectionWithType]):
        self._collections = collections_with_type

        self._source_imagery = None
        self._labels = None

    def __iter__(self) -> Iterator[Collection]:
        for item in self._collections:
            yield item.collection

    def __len__(self) -> int:
        return len(self._collections)

    def __getitem__(self, item: int) -> Collection:
        return self._collections[item].collection

    def __repr__(self) -> str:
        return list(self.__iter__()).__repr__()

    @property
    def source_imagery(self) -> List[Collection]:
        if self._source_imagery is None:
            self._source_imagery = [
                c.collection
                for c in self._collections
                if any(type_ is CollectionType.SOURCE for type_ in c.types)
            ]
        return self._source_imagery

    @property
    def labels(self) -> List[Collection]:
        if self._labels is None:
            self._labels = [
                c.collection
                for c in self._collections
                if any(type_ is CollectionType.LABELS for type_ in c.types)
            ]
        return self._labels
