"""Extensions of the `PySTAC <https://pystac.readthedocs.io/en/latest/>`_ classes that provide convenience methods for interacting
with the `Radiant MLHub API <https://docs.mlhub.earth/#radiant-mlhub-api>`_."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union, cast

import pystac.catalog
import pystac.collection
import pystac.item
import pystac.link
import pystac.provider
import pystac.summaries

from .. import client
from ..exceptions import EntityDoesNotExist

TagOrTagList = Union[str, Iterable[str]]
TextOrTextList = Union[str, Iterable[str]]


class Collection(pystac.collection.Collection):
    """Class inheriting from :class:`pystac.Collection` that adds some convenience methods for listing and fetching
    from the Radiant MLHub API.
    """
    _archive_size: Optional[int]

    def __init__(
        self,
        id: str,
        description: str,
        extent: pystac.collection.Extent,
        title: Optional[str] = None,
        stac_extensions: Optional[List[str]] = None,
        href: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
        catalog_type: Optional[pystac.catalog.CatalogType] = None,
        license: str = "proprietary",
        keywords: Optional[List[str]] = None,
        providers: Optional[List[pystac.provider.Provider]] = None,
        summaries: Optional[pystac.summaries.Summaries] = None,
        *,
        api_key: Optional[str] = None,
        profile: Optional[str] = None,
    ):
        super().__init__(id, description, extent, title=title, stac_extensions=stac_extensions, href=href,
                         extra_fields=extra_fields, catalog_type=catalog_type, license=license, keywords=keywords,
                         providers=providers, summaries=summaries)

        self.session_kwargs = {}
        if api_key is not None:
            self.session_kwargs['api_key'] = api_key
        if profile is not None:
            self.session_kwargs['profile'] = profile

        # Use -1 here instead of None because None represents the case where the archive does not
        #  exist (HEAD returns a 404).
        self._archive_size = -1

    @classmethod
    def list(cls, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> List['Collection']:
        """Returns a list of :class:`Collection` instances for all collections hosted by MLHub.

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
        collections : List[Collection]
        """
        return [
            cls.from_dict(collection)
            for collection in client.list_collections(api_key=api_key, profile=profile)
        ]

    @classmethod
    def from_dict(
        cls,
        d: Dict[str, Any],
        href: Optional[str] = None,
        root: Optional[pystac.catalog.Catalog] = None,
        migrate: bool = False,
        preserve_dict: bool = True,
        *,
        api_key: Optional[str] = None,
        profile: Optional[str] = None
    ) -> "Collection":
        """Patches the :meth:`pystac.Collection.from_dict` method so that it returns the calling class instead of always returning
        a :class:`pystac.Collection` instance."""
        catalog_type = pystac.catalog.CatalogType.determine_type(d)

        d = deepcopy(d)
        id_ = d.pop('id')
        description = d.pop('description')
        license_ = d.pop('license')
        extent = pystac.collection.Extent.from_dict(d.pop('extent'))
        title = d.get('title')
        stac_extensions = d.get('stac_extensions')
        keywords = d.get('keywords')
        providers = d.get('providers')
        if providers is not None:
            providers = list(map(
                lambda x: cast(object, pystac.provider.Provider.from_dict(x)),
                providers
            ))
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
            summaries=summaries,
            href=href,
            catalog_type=catalog_type,
            api_key=api_key,
            profile=profile
        )

        for link in links:
            if link['rel'] == 'root':
                # Remove the link that's generated in Catalog's constructor.
                collection.remove_links('root')

            if link['rel'] != 'self' or href is None:
                collection.add_link(pystac.link.Link.from_dict(link))

        return collection

    @classmethod
    def fetch(cls, collection_id: str, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> 'Collection':
        """Creates a :class:`Collection` instance by fetching the collection with the given ID from the Radiant MLHub API.

        Parameters
        ----------
        collection_id : str
            The ID of the collection to fetch (e.g. ``bigearthnet_v1_source``).
        api_key : str
            An API key to use for this request. This will override an API key set in a profile on using
            an environment variable
        profile: str
            A profile to use when making this request.

        Returns
        -------
        collection : Collection
        """
        response = client.get_collection(collection_id, api_key=api_key, profile=profile)
        return cls.from_dict(response, api_key=api_key, profile=profile)

    def get_items(self, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> Iterator[pystac.item.Item]:
        """
        .. note::

            The ``get_items`` method is not implemented for Radiant MLHub :class:`Collection` instances for performance reasons. Please use
            the :meth:`Collection.download` method to download Collection assets.

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError('For performance reasons, the get_items method has not been implemented for Collection instances. Please '
                                  'use the Collection.download method to download Collection assets.')

    def fetch_item(self, item_id: str, *, api_key: Optional[str] = None, profile: Optional[str] = None) -> pystac.item.Item:
        api_key = api_key or self.session_kwargs.get("api_key")
        profile = profile or self.session_kwargs.get("profile")
        response = client.get_collection_item(self.id, item_id, api_key=api_key, profile=profile)
        return pystac.item.Item.from_dict(response)

    def download(
            self,
            output_dir: Union[str, Path],
            *,
            if_exists: str = 'resume',
            api_key: Optional[str] = None,
            profile: Optional[str] = None
    ) -> Path:
        """Downloads the archive for this collection to an output location (current working directory by default). If the parent directories
        for ``output_path`` do not exist, they will be created.

        The ``if_exists`` argument determines how to handle an existing archive file in the output directory. See the documentation for
        the :func:`~radiant_mlhub.client.download_archive` function for details. The default behavior is to resume downloading if the
        existing file is incomplete and skip the download if it is complete.

        .. note::

            Some collections may be very large and take a significant amount of time to download, depending on your connection speed.

        Parameters
        ----------
        output_dir : Path
            Path to a local directory to which the file will be downloaded. File name will be generated
            automatically based on the download URL.
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
        output_path : pathlib.Path
            The path to the downloaded archive file.

        Raises
        ------
        FileExistsError
            If file at ``output_path`` already exists and both ``exist_okay`` and ``overwrite`` are ``False``.
        """
        session_kwargs = {
            **self.session_kwargs,
            "api_key": api_key,
            "profile": profile
        }
        return client.download_archive(self.id, output_dir=os.fspath(output_dir), if_exists=if_exists, **session_kwargs)

    @property
    def registry_url(self) -> Optional[str]:
        """The URL of the registry page for this Collection. The URL is based on the DOI identifier
        for the collection. If the Collection does not have a ``"sci:doi"`` property then
        ``registry_url`` will be ``None``."""

        # Some Collections don't publish the "scientific" extension in their "stac_extensions"
        # attribute so we access this via "extra_fields" rather than through self.ext["scientific"].
        doi = self.extra_fields.get("sci:doi")
        if doi is None:
            return None

        return f'https://registry.mlhub.earth/{doi}'

    @property
    def archive_size(self) -> Optional[int]:
        """The size of the tarball archive for this collection in bytes (or ``None`` if the archive
        does not exist)."""

        # Use -1 here instead of None because None represents the case where the archive does not
        #  exist (HEAD returns a 404).
        if self._archive_size == -1:
            try:
                self._archive_size = client.get_archive_info(self.id, **self.session_kwargs).get('size')
            except EntityDoesNotExist:
                self._archive_size = None

        return self._archive_size
