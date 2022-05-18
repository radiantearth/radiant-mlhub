Getting Started
===============


This guide will walk you through the basic usage of the ``radiant_mlhub`` library, including:

* Installing & configuring the library
* Discovering & fetching datasets
* Discovering & fetching collections
* Downloading dataset STAC catalog and assets

Background Info
+++++++++++++++

If you have not already, browse `Radiant MLHub <https://mlhub.earth>`_ to
discover the datasets and ML models which are currently published on MLHub.
Consider browsing the `STAC specification <https://stacspec.org>`_ to learn
about SpatioTemporal Asset Catalogs (STAC). The MLHub API serves STAC
Collections, Items and Assets.

Installation
++++++++++++

Install with ``pip``
--------------------

.. code-block:: console

    $ pip install radiant_mlhub

Install with ``conda``
----------------------

.. code-block:: console

    $ conda install -c conda-forge radiant-mlhub

Configuration
+++++++++++++

If you have not done so already, you will need to register for an MLHub API key 
at `https://mlhub.earth <https://mlhub.earth/profile>`_.

Once you have your API key, you will need to create a default profile by setting up a ``.mlhub/profiles`` file in your
home directory. You can use the :ref:`mlhub configure <configure>` command line tool to do this:

.. code-block:: console

    $ mlhub configure
    API Key: Enter your API key here...
    Wrote profile to /home/user/.mlhub/profiles

.. hint::

    If you do not have write access to the home directory on your machine, you can change the location of the ``profiles`` file using the ``MLHUB_HOME``
    environment variables. For instance, setting ``MLHUB_HOME=/tmp/some-directory/.mlhub`` will cause the client to look for your profiles in a
    ``/tmp/some-directory/.mlhub/profiles`` file. You may want to permanently set this environment variable to ensure the client continues to look in
    the correct place for your profiles.

List Datasets
+++++++++++++++++

Once you have your profile configured, you can get a list of the available datasets from the Radiant MLHub API using the
:meth:`Dataset.list <radiant_mlhub.models.Dataset.list>` method. Remember that all datasets are also browseable and searchable on
`Radiant MLHub <https://mlhub.earth/datasets>`_.

.. code-block:: python

    >>> from radiant_mlhub import Dataset
    >>> datasets = Dataset.list()
    >>> # print the first 5 datasets for example
    >>> for dataset in datasets[0:5]:
    ...     print(dataset)
    umd_mali_crop_type: 2019 Mali CropType Training Data
    idiv_asia_crop_type: A crop type dataset for consistent land cover classification in Central Asia
    dlr_fusion_competition_germany: A Fusion Dataset for Crop Type Classification in Germany
    ref_fusion_competition_south_africa: A Fusion Dataset for Crop Type Classification in Western Cape, South Africa
    bigearthnet_v1: BigEarthNet

Fetch a Dataset
+++++++++++++++

You can also fetch a dataset by ID using the :meth:`Dataset.fetch <radiant_mlhub.models.Dataset.fetch>` method. This method returns a
:class:`~radiant_mlhub.models.Dataset` instance.

.. code-block:: python

    >>> dataset = Dataset.fetch('bigearthnet_v1')
    >>> print(dataset)
    bigearthnet_v1: BigEarthNet V1

Work with Dataset Collections
+++++++++++++++++++++++++++++

Datasets have one or more collections associated with them. Collections fall
into two types:

* ``source_imagery``: Collections of source imagery associated with the dataset
* ``labels``: Collections of labeled data associated with the dataset (these collections implement the
  `STAC Label Extension <https://github.com/radiantearth/stac-spec/tree/master/extensions/label>`_)

To list all the collections associated with a dataset use the :attr:`~radiant_mlhub.models.Dataset.collections` attribute.

.. code-block:: python

    >>> dataset.collections
    [<Collection id=bigearthnet_v1_source>, <Collection id=bigearthnet_v1_labels>]
    >>> type(dataset.collections[0])
    radiant_mlhub.models.collection.Collection

You can also list the collections by type using the ``collections.source_imagery`` and ``collections.labels`` properties.
This example code shows that collections are actually `STAC objects <https://stacspec.org/>`_.

.. code-block:: python

    >>> from pprint import pprint
    >>> len(dataset.collections.source_imagery)
    1
    >>> source_collection = dataset.collections.source_imagery[0]
    >>> pprint(source_collection.to_dict())
    {'description': 'BigEarthNet v1.0',
    'extent': {'spatial': {'bbox': [[-9.00023345437725,
                                    36.956956702083396,
                                    31.598439091981028,
                                    68.02168200047284]]},
                'temporal': {'interval': [['2017-06-13T10:10:31Z',
                                        '2018-05-29T11:54:01Z']]}},
    'id': 'bigearthnet_v1_source',
    'license': 'CDLA-Permissive-1.0',
    'links': [{'href': 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source/items',
                'rel': 'items',
                'type': 'application/geo+json'},
            {'href': 'https://api.radiant.earth/mlhub/v1/',
                'rel': 'parent',
                'type': 'application/json'},
            {'href': 'https://api.radiant.earth/mlhub/v1/',
                'rel': <RelType.ROOT: 'root'>,
                'title': 'Radiant MLHub API',
                'type': <MediaType.JSON: 'application/json'>},
            {'href': 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source',
                'rel': 'self',
                'type': 'application/json'}],
    'providers': [{'name': 'BigEarthNet',
                    'roles': ['processor', 'licensor'],
                    'url': 'http://bigearth.net'}],
    'sci:citation': 'G. Sumbul, M. Charfuelan, B. Demir, V. Markl, "BigEarthNet: '
                    'A Large-Scale Benchmark Archive for Remote Sensing Image '
                    'Understanding", IEEE International Geoscience and Remote '
                    'Sensing Symposium, pp. 5901-5904, Yokohama, Japan, 2019.',
    'sci:doi': '10.14279/depositonce-10149',
    'stac_extensions': ['https://stac-extensions.github.io/scientific/v1.0.0/schema.json'],
    'stac_version': '1.0.0',
    'type': 'Collection'}

Download a Dataset
++++++++++++++++++

You can download a dataset's STAC catalog, and all of it's linked assets, using the
:meth:`Dataset.download <radiant_mlhub.models.Dataset.download>` method. Consider
checking the dataset size before downloading.  Here is an example dataset which
is relatively small in size. The downloader can also scale up to the largest datasets.

.. code-block:: python

    >>> dataset = Dataset.fetch('nasa_marine_debris')
    >>> print(dataset)
    nasa_marine_debris: Marine Debris Dataset for Object Detection in Planetscope Imagery
    >>> print(dataset.stac_catalog_size)  # OK the STAC catalog archive is only ~260KB
    263582
    >>> print(dataset.estimated_dataset_size)  # OK the total dataset assets are ~77MB
    77207762
    >>> dataset.download()
    nasa_marine_debris: fetch stac catalog: 258KB [00:00, 404.83KB/s]                                                                                                        
    unarchive nasa_marine_debris.tar.gz: 100%|█████████████████████████████████████████████████████████████████████████████████████████| 2830/2830 [00:00<00:00, 4744.75it/s]
    download assets: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████| 2825/2825 [03:48<00:00, 12.36it/s]

The :meth:`Dataset.download <radiant_mlhub.models.Dataset.download>` method
saves the STAC catalog and assets into your current working directory (by default).

The downloader has the ability to download in parallel with many cores, resume
interrupted downloads, as well as options for filtering the assets to a more
manageable size (highly recommended, depending on your application).

* :ref:`Filter by Collection and Asset Keys`
* :ref:`Filter by Temporal Range`
* :ref:`Filter by Bounding Box`
* :ref:`Filter by GeoJSON Area of Interest`

.. hint::
    The :ref:`Datasets` guide has more downloading examples
    and the :func:`Dataset.download <radiant_mlhub.models.Dataset.download>`
    API reference is available as well.

.. hint::
    The :ref:`Collections` guide has examples of downloading collection
    archives. Collection archives are not available for all collections, so
    consider using the Dataset downloader instead.

Discovering ML Models
+++++++++++++++++++++

ML Models are discoverable through the Python client as well.
See the :ref:`ML Models` guide for more information.
