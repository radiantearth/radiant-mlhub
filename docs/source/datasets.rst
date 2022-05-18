Datasets
========

A **dataset** represents a group of 1 or more related STAC Collections. They
group together any source imagery collections with the associated label
collections to provide a convenient mechanism for accessing all of these data
together. For instance, the ``bigearthnet_v1_source`` collection contains the
source imagery for the `BigEarthNet <http://bigearth.net/>`_ training dataset
and, likewise, the ``bigearthnet_v1_labels`` ollection contains the
annotations for that same dataset. These 2 collections are grouped together
into the ``bigearthnet_v1`` dataset.

`Radiant MLHub <https://mlhub.earth/>`_ provides an overview of the datasets
available through the Radiant MLHub API along with dataset metadata and a
listing of the associated collections.

To list and fetch datasets, the :class:`~radiant_mlhub.models.Dataset` class is
the recommended approach, but there are also low-level client methods from
:mod:`radiant_mlhub.client`. Both methods are described below.

.. hint::
    The `Radiant MLHub <https://mlhub.earth/>`_ web application provides an
    overview of all the datasets and collections available through the Radiant
    MLHub API.

.. note::
    The objects returned by the Radiant MLHub API Dataset endpoints are not
    STAC-compliant objects and therefore the
    :class:`Dataset <radiant_mlhub.models.Dataset>` class described below is not
    a :doc:`PySTAC <pystac:index>` object.

Discovering Datasets
++++++++++++++++++++

You can discover datasets using the
:meth:`Dataset.list <radiant_mlhub.models.Dataset.list>` method. This method
returns a list of :class:`Dataset <radiant_mlhub.models.Dataset>` instances.

.. code-block:: python

    >>> from radiant_mlhub import Dataset
    >>> datasets = Dataset.list()
    >>> for dataset in datasets[0:5]:  # print first 5 datasets, for example
    >>>     print(dataset)
    umd_mali_crop_type: 2019 Mali CropType Training Data
    idiv_asia_crop_type: A crop type dataset for consistent land cover classification in Central Asia
    dlr_fusion_competition_germany: A Fusion Dataset for Crop Type Classification in Germany
    ref_fusion_competition_south_africa: A Fusion Dataset for Crop Type Classification in Western Cape, South Africa
    bigearthnet_v1: BigEarthNet

The ``list()`` method also accepts ``tags`` and ``text`` arguments that can be
used to filter datasets by their tags or a free text search, respectively. The
``tags`` argument may be either a single string or a list of strings. Only
datasets that contain all of provided tags will be returned and these tags must
be an `exact` match. The `text` argument may, similarly, be either a string or
a list of strings. These will be used to search all of the text-based metadata
fields for a dataset (e.g. description, title, citation, etc.). Each argument
is treated as a phrase by the text search engine and only datasets with matches
for all of the provided phrases will be returned. So, for instance,
``text=["maize", "rice"]`` will return all datasets with either ``"maize"`` or
``"rice"`` somewhere in their text metadata, while ``text=["maize rice"]`` will
not match any datasets. The search ``text="land cover"`` will return all
datasets with the `phrase` ``"land cover"`` in their text metadata.

Low-level client
----------------

The Radiant MLHub ``/datasets`` endpoint returns a list of objects describing
the available datasets and their associated collections. You can use the
low-level :func:`~radiant_mlhub.client.list_datasets` function to work with
these responses as native Python data types (:class:`list` and :class:`dict`).

.. code-block:: python

    >>> from radiant_mlhub.client import list_datasets
    >>> from pprint import pprint
    >>> datasets = list_datasets()
    >>> first_dataset = datasets[0]
    >>> pprint(first_dataset)
    {'id': 'umd_mali_crop_type',
    'title': '2019 Mali CropType Training Data',
    ...

Fetching Dataset Metadata
+++++++++++++++++++++++++

You can fetch a dataset from the Radiant MLHub API based on the dataset ID using the :meth:`Dataset.fetch <radiant_mlhub.models.Dataset.fetch>`
method. This method returns a :class:`~radiant_mlhub.models.Dataset` instance.
Fetching returns the metadata but does not download assets.

.. code-block:: python

    >>> dataset = Dataset.fetch_by_id('bigearthnet_v1')
    >>> print(dataset.id)
    bigearthnet_v1: BigEarthNet

If you would rather fetch the dataset using its `DOI <https://www.doi.org/>`__
you can do so as well:

.. code-block:: python

    dataset = Dataset.fetch_by_doi("10.6084/m9.figshare.12047478.v2")

You can also use the more general :meth:`Dataset.fetch<radiant_mlhub.models.Dataset.fetch>` method to get a dataset using either ID or DOI.

.. code-block:: python

    from radiant_mlhub.client import get_dataset
    # These will all return the same dataset
    dataset = Dataset.fetch("ref_african_crops_kenya_02")
    dataset = Dataset.fetch("10.6084/m9.figshare.12047478.v2")

Low-level client
----------------

The Radiant MLHub ``/datasets/{dataset_id}`` endpoint returns an object
representing a single dataset. You can use the low-level
:func:`~radiant_mlhub.client.get_dataset` function to work with this response
as a :class:`dict`.

.. code-block:: python

    >>> from radiant_mlhub.client import get_dataset_by_id
    >>> dataset = get_dataset_by_id('bigearthnet_v1')
    >>> pprint(dataset)
    {'collections': [{'id': 'bigearthnet_v1_source', 'types': ['source_imagery']},
                 {'id': 'bigearthnet_v1_labels', 'types': ['labels']}],
     'id': 'bigearthnet_v1',
     'title': 'BigEarthNet V1'}

Dataset Collections
+++++++++++++++++++

If you are using the :class:`~radiant_mlhub.models.Dataset` class, you can list the Collections associated with the dataset using the
:attr:`Dataset.collections <radiant_mlhub.models.Dataset.collections>` property. This method returns a modified :class:`list` that has
2 additional attributes: ``source_imagery`` and ``labels``. You can use these attributes to list only the collections of a the associated type.
All elements of these lists are instances of :class:`~radiant_mlhub.models.Collection`. See the :ref:`Collections` documentation for
details on how to work with these instances.

.. code-block:: python

    >>> len(first_dataset.collections)
    2
    >>> len(first_dataset.collections.source_imagery)
    1
    >>> first_dataset.collections.source_imagery[0].id
    'umd_mali_crop_type_source'
    >>> len(first_dataset.collections.labels)
    1
    >>> first_dataset.collections.labels[0].id
    'umd_mali_crop_type_source'

.. warning::

    There are rare cases of collections that contain both ``source_imagery``
    and ``labels`` items (e.g. the SpaceNet collections). In these cases, the
    collection will be listed in both the ``dataset.collections.labels`` and
    ``dataset.collections.source_imagery`` lists, but *will only appear once in
    the main ``dataset.collections`` list*. This may cause what appears to be a
    mismatch in list lengths:

    .. code-block:: python

        >>> len(dataset.collections.source_imagery) + len(dataset.collections.labels) == len(dataset.collections)
        False

.. note::

    Both the class methods and the low-level client functions
    accept keyword arguments that are passed directly to
    :func:`~radiant_mlhub.session.get_session` to create a session. See the
    :ref:`Authentication` documentation for details on how to use these
    arguments or configure the client to read your API key automatically.

Downloading Datasets
++++++++++++++++++++

The dataset downloader offers download of STAC catalog archives, linked
dataset assets, as well as partial downloads with filtering options.

* Robustness
    * Asset download resuming.
    * Retry and backoff for http error conditions.
    * Error reporting for unrecoverable download errors.
* Performance
    * Scales to millions of assets.
    * Multithreaded workers: parallel downloads.
* Convenience
    * STAC collection_id and item asset key filter
    * Temporal filter
    * Bounding box filter
    * GeoJSON intersection filter

Download All Assets
-------------------

The most basic usage is to fetch a dataset, and then call it's download method.
The output directory is the current working directory (by default).

.. code-block:: python

    >>> from radiant_mlhub.models import Dataset
    >>> nasa_marine_debris = Dataset.fetch_by_id('nasa_marine_debris')
    >>> print(nasa_marine_debris)
    nasa_marine_debris: Marine Debris Dataset for Object Detection in Planetscope Imagery
    >>> nasa_marine_debris.download()
    nasa_marine_debris: fetch stac catalog: 258KB [00:00, 75252.46KB/s]                                                     
    unarchive nasa_marine_debris.tar.gz: 100%|████████████████████████████████████| 2830/2830 [00:00<00:00, 14185.00it/s]
    download assets: 100%|█████████████████████████████████████████████████████████████| 2825/2825 [00:19<00:00, 145.36it/s]

Logging
-------

The Python logging module can be used to control the verbosity of the download. Turn in INFO or DEBUG messages to see additional messages:

.. code-block:: python

    >>> import logging
    >>> logging.basicConfig(level=logging.INFO)
    >>> nasa_marine_debris.download()
    nasa_marine_debris: fetch stac catalog: 258KB [00:00, 34940.12KB/s]                                                     
    INFO:radiant_mlhub.client.catalog_downloader:unarchive nasa_marine_debris.tar.gz...
    unarchive nasa_marine_debris.tar.gz: 100%|████████████████████████████████████| 2830/2830 [00:00<00:00, 14191.09it/s]
    INFO:radiant_mlhub.client.catalog_downloader:create stac asset list...
    INFO:radiant_mlhub.client.catalog_downloader:2825 unique assets in stac catalog.
    download assets: 100%|█████████████████████████████████████████████████████████████| 2825/2825 [00:18<00:00, 152.37it/s]
    INFO:radiant_mlhub.client.catalog_downloader:assets saved to /home/user/nasa_marine_debris

Output Directory
----------------

The output directory is by default, the current working directory. The
``output_dir`` parameter takes a ``str`` or ```pathlib.Path``. It will be
created if it does not exist.

.. code-block:: python

    # output_dir as string
    nasa_marine_debris.download(output_dir='/tmp')

    # output_dir as Path object
    from pathlib import Path
    nasa_marine_debris.download(output_dir=Path.home() / 'my_projects' / 'ml_datasets')

Large Dataset Performance
-------------------------

Let's try a bit larger dataset (tens of thousands of assets). After downloading
the complete dataset, we'll explore all of the options for filtering assets.
Filtering lets you limit the items and assets to those you are interested in
prior to downloading.

This download example was run on a compute-optimized 16-core virtual machine in
the MS Azure West-Europe region. You would likely experience slower download
performance on your machine, depending on number of cores and network
bandwidth.

.. code-block:: python

    >>> sen12floods = Dataset.fetch_by_id('sen12floods')
    >>> %%time
    >>> sen12floods.download()
    sen12floods: fetch stac catalog: 2060KB [00:00, 127699.36KB/s]                                                          
    INFO:radiant_mlhub.client.catalog_downloader:unarchive sen12floods.tar.gz...
    unarchive sen12floods.tar.gz: 100%|█████████████████████████████████████████| 22278/22278 [00:01<00:00, 14239.53it/s]
    INFO:radiant_mlhub.client.catalog_downloader:create stac asset list...
    INFO:radiant_mlhub.client.catalog_downloader:39063 unique assets in stac catalog.
    download assets: 100%|███████████████████████████████████████████████████████████| 39063/39063 [06:26<00:00, 101.06it/s]
    INFO:radiant_mlhub.client.catalog_downloader:assets saved to /home/user/sen12floods

    CPU times: user 11min 44s, sys: 2min 15s, total: 14min
    Wall time: 6min 40s

15GB of assets were downloaded into the ``sen12floods/`` directory.
You may not necessarily want to download all of the assets in a dataset.
In the following sections, all the filtering options are explained.

.. hint::

    Download filters may be freely combined, except ``bbox`` and ``intersects``
    which are independent options.

Checking Dataset Size
---------------------

Consider checking the dataset size before downloading.

.. code-block:: python

    >>> dataset = Dataset.fetch('nasa_marine_debris')
    >>> print(dataset)
    nasa_marine_debris: Marine Debris Dataset for Object Detection in Planetscope Imagery
    >>> print(dataset.stac_catalog_size)  # OK the STAC catalog archive is only ~260KB
    263582
    >>> print(dataset.estimated_dataset_size)  # OK the total dataset assets are ~77MB
    77207762

Filter by Collection and Asset Keys
-----------------------------------

To download only the specified STAC collection ids and STAC item asset keys,
create a dictionary in this format and pass it to the ``collection_filter``
parameter:

``{ collection_id1: [ asset_key1, asset_key2, ...], collection_id2: [asset_key1, asset_key2, ...] , ... }``

For example, using the ``sen12floods`` dataset, if we only wanted to download
four bands of the source imagery:

.. code-block:: python

    my_filter = dict(
        sen12floods_s2_source=['B02', 'B03', 'B04', 'B08'],   # Red, Green, Blue, NIR
        sen12floods_s2_labels=['labels', 'documentation'], 
    )
    sen12floods.download(collection_filter=my_filter)


Filter by Temporal Range
------------------------

To download only STAC assets within a temporal range, use ``datetime`` parameter
to specify a datetime range (tuple of ``datetime`` objects), or a single day (single
``datetime`` object).

.. code-block:: python

    from dateutil.parser import parse
    my_start_date=parse("2019-04-01T00:00:00+0000")
    my_end_date=parse("2019-04-07T00:00:00+0000")
    sen12floods.download(datetime=(my_start_date, my_end_date))

Filter by Bounding Box
-------------------------------------

To download only STAC assets with a spatial bounding box, use the ``bbox``
parameter to specify a bounding box in lat/lng (CRS EPSG:4326). This performs a
spatial intersection test with each STAC item's bounding box.

.. code-block:: python

    my_bbox = [-13.278254, 8.447033,
               -13.231551, 8.493532]
    sen12floods.download(bbox=my_bbox)

.. hint::
    The ``bbox`` filter may not be used with the ``intersects`` filter (use one
    or the other).

Filter by GeoJSON Area of Interest
----------------------------------

To download only STAC assets within an area of interest, use the ``intersects``
parameter. This performs a spatial intersection test with each STAC item's
bounding box.

.. code-block:: python

    import json
    my_geojson = json.loads(
        """
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            -13.278048,
                            8.493532
                        ],
                        [
                            -13.278254,
                            8.447241
                        ],
                        [
                            -13.231762,
                            8.447033
                        ],
                        [
                            -13.231551,
                            8.493323
                        ],
                        [
                            -13.278048,
                            8.493532
                        ]
                    ]
                ]           
            }
        }
        """
    )
    sen12floods.download(intersects=my_geojson)

.. hint::

   The ``intersects`` filter may not be used with the ``bbox`` filter (use one or the other).


STAC Catalog Only download
--------------------------

If you want to inspect the STAC catalog or write your own download client for
the assets just pass the ``catalog_only`` option to the download method:

.. code-block:: python

    >>> sen12floods.download(catalog_only=True)
    sen12floods: fetch stac catalog: 2060KB [00:00, 127903.52KB/s]                                                          
    INFO:radiant_mlhub.client.catalog_downloader:unarchive sen12floods.tar.gz...
    unarchive sen12floods.tar.gz: 100%|█████████████████████████████████████████| 22278/22278 [00:01<00:00, 14284.65it/s]
    INFO:radiant_mlhub.client.catalog_downloader:catalog saved to /home/user/sen12floods

Error reporting
---------------

Any unrecoverable download errors will be logged to ``{output_dir}/err_report.csv``
and a Python exception will be raised.

Appendix: Filesystem Layout of Downloads
----------------------------------------

STAC archive file:

    ``{output_dir}/{dataset_id}.tar.gz``

Unarchived STAC catalog:

    ``{output_dir}/{dataset_id}/catalog.json``

Collection, Item and Asset layout:

    ``{output_dir}/{dataset_id}/{collection_id}/{item_id}/{asset_key}.{ext}``

Common Assets, ex: documentation.pdf are saved into a _common directory instead of duplicating them for many items:

    ``{output_dir}/{dataset_id}/_common/{asset_key}.{ext}``

Asset Database:

    ``{output_dir}/{dataset_id}/mlhub_stac_assets.db``

.. hint::
    The ``mlhub_stac_assets.db`` file is an artifact which may be safely deleted to free up disk space.
