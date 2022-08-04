Collections
===========

A **collection** represents either a group of related labels or a group of
related source imagery for a given time period and geographic area. All
collections in the Radiant MLHub API are valid `STAC Collections
<https://github.com/radiantearth/stac-spec/tree/master/collection-spec>`_. For
instance, the ``umd_mali_crop_type_source`` collection catalogs the source
imagery associated with the 2019 Mali CropType dataset, while the
``umd_mali_crop_type_labels`` collection catalogs the land cover labels
associated with this imagery. These collections are considered part of a single
``umd_mali_crop_type`` **dataset** (see the :ref:`Datasets` documentation for
details on working with datasets).

.. hint::
    The `Radiant MLHub <https://mlhub.earth/>`_ web application provides an
    overview of all the datasets and collections available through the Radiant
    MLHub API.

.. note::
    Collections are grouped into Datasets. See also the :ref:`Datasets` guide
    for more information about finding and downloading Datasets.

To list and fetch collections, the :class:`~radiant_mlhub.models.Collection`
class is the recommended approach, but there are also low-level client methods
from :mod:`radiant_mlhub.client`. Both methods are described below.

Discovering Collections
+++++++++++++++++++++++

You can discover collections using the
:meth:`Collection.list <radiant_mlhub.models.Collection.list>` method.
This method returns a list of :class:`Collection <radiant_mlhub.models.Collection>` instances.

.. code-block:: python

    >>> from radiant_mlhub import Collection
    >>> collections = Collection.list()
    >>> first_collection = collections[0]
    >>> print(first_collection)
    ref_landcovernet_sa_v1_source_landsat_8: LandCoverNet South America Landsat 8 Source Imagery

Low-level client
----------------

The Radiant MLHub ``/collections`` endpoint returns a list of objects
describing the available collections. You can use the low-level
:func:`~radiant_mlhub.client.list_collections` function to work with these
responses as native Python data types (:class:`list` and :class:`dict`). This
function returns a list of JSON-like dictionaries representing STAC
Collections.

.. code-block:: python

    >>> from radiant_mlhub.client import list_collections
    >>> from pprint import pprint
    >>> collections = list_collections()
    >>> first_collection = collections[0]
    >>> pprint(first_collection)
    {'description': 'LandCoverNet South America Landsat 8 Source Imagery',
     'id': 'ref_landcovernet_sa_v1_source_landsat_8',
     ...

Fetching Collection Metadata
++++++++++++++++++++++++++++

You can fetch a collection from the Radiant MLHub API based on the collection
ID using the :meth:`Collection.fetch <radiant_mlhub.models.Collection.fetch>`
method. This is the recommended way of fetching a collection. This method
returns a :class:`~radiant_mlhub.models.Collection` instance. Fetching returns
the metadata but does not download assets.

.. code-block:: python

    >>> collection = Collection.fetch('ref_african_crops_kenya_01_labels')
    >>> print(collection)
    ref_african_crops_kenya_01_labels: African Crops Kenya

For more information on a collection, you can browse to the MLHub page for the
related dataset, for example:

.. code-block:: python

    >>> print(collection.registry_url)
    https://registry.mlhub.earth/10.34911/rdnt.u41j87

Browse to https://registry.mlhub.earth/10.34911/rdnt.u41j87

Low-level client
----------------

The Radiant MLHub ``/collections/{id}`` endpoint returns an object representing
a single collection's metadata. You can use the low-level
:func:`~radiant_mlhub.client.get_collection` function to work with this
response as a :class:`dict`.

.. code-block:: python

    >>> from radiant_mlhub.client import get_collection
    >>> collection = get_collection('ref_african_crops_kenya_01_labels')
    >>> pprint(collection)
    {'description': 'African Crops Kenya',
    'extent': {'spatial': {'bbox': [[34.18191992149459,
                                    0.4724181558451209,
                                    34.3714943155646,
                                    0.7144217206851109]]},
                'temporal': {'interval': [['2018-04-10T00:00:00Z',
                                        '2020-03-13T00:00:00Z']]}},
    'id': 'ref_african_crops_kenya_01_labels',
    ...

Downloading a Collection
++++++++++++++++++++++++

.. note::
    Not all collections have downloadable archives (depending on size).
    Consider instead using the dataset downloader functionality. The
    :ref:`Datasets` guide has more examples and the :func:`Dataset.download
    <radiant_mlhub.models.Dataset.download>` API reference is available as
    well.

You can download a collection archive using the :meth:`Collection.download
<radiant_mlhub.models.Collection.download>` method. This is the recommended way
of downloading a collection archive.

.. hint::
    To check the existence, and size of the download archive without actually
    downloading it, you can use the :attr:`Collection.archive_size` property,
    which returns a size in bytes.

.. code-block:: python

    >>> collection = Collection.fetch('sn1_AOI_1_RIO')
    >>> collection.archive_size
    3504256089
    >>> archive_path = collection.download('~/Downloads')
    28%|██▊       | 985.0/3496.9 [00:35<00:51, 48.31M/s]
    >>> archive_path
    PosixPath('/Users/someuser/Downloads/sn1_AOI_1_RIO.tar.gz')

If a file of the same name already exists, these methods will check whether the
downloaded file is complete by comparing its size against the size of the
remote file. If they are the same size, the download is skipped, otherwise the
download will be resumed from the point where it stopped. You can control this
behavior using the ``if_exists`` argument. Setting this to ``"skip"`` will skip
the download for existing files *without* checking for completeness (a bit
faster since it doesn't require a network request), and setting this to
``"overwrite"`` will overwrite any existing file.

Collection archives are gzipped tarballs. You can read more about the structure of
these archives in `this Medium post <https://medium.com/radiant-earth-insights/archived-training-dataset-downloads-now-available-on-radiant-mlhub-7eb67daf094e>`_.

Low-level client
----------------

The Radiant MLHub ``/archive/{archive_id}`` endpoint allows you to download an
archive of all assets associated with a given collection. You can use the
low-level :func:`~radiant_mlhub.client.download_collection_archive` function to download
the archive to your local file system.

.. code-block:: python

    >>> from radiant_mlhub.client import download_collection_archive
    >>> archive_path = download_collection_archive('sn1_AOI_1_RIO')
    28%|██▊       | 985.0/3496.9 [00:35<00:51, 48.31M/s]
    >>> archive_path
    PosixPath('/path/to/current/directory/sn1_AOI_1_RIO.tar.gz')
