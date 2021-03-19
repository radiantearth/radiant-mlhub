Getting Started
===============

This guide will walk you through the basic usage of the ``radiant_mlhub`` library, including:

* Installing & configuring the library
* Discovering & fetching datasets
* Discovering & fetching collections
* Downloading assets

Installation
++++++++++++

.. code-block:: console

    $ pip install radiant_mlhub

Configuration
+++++++++++++

If you have not done so already, you will need to register for an MLHub API key `here <http://dashboard.mlhub.earth/>`_.

Once you have your API key, you will need to create a default profile by setting up a ``.mlhub/profiles`` file in your
home directory. You can use the :ref:`mlhub configure <configure>` command line tool to do this:

.. code-block:: console

    $ mlhub configure
    API Key: Enter your API key here...
    Wrote profile to /Users/youruser/.mlhub/profiles

.. hint::

    If you do not have write access to the home directory on your machine, you can change the location of the ``profiles`` file using the ``MLHUB_HOME``
    environment variables. For instance, setting ``MLHUB_HOME=/tmp/some-directory/.mlhub`` will cause the client to look for your profiles in a
    ``/tmp/some-directory/.mlhub/profiles`` file. You may want to permanently set this environment variable to ensure the client continues to look in
    the correct place for your profiles.

List Datasets
+++++++++++++++++

Once you have your profile configured, you can get a list of the available datasets from the Radiant MLHub API using the
:meth:`Dataset.list <radiant_mlhub.models.Dataset.list>` method. This method is a :term:`generator` that yields
:class:`~radiant_mlhub.models.Dataset` instances. You can use the ``id`` and ``title`` properties to get more information about a dataset.

.. code-block:: python

    >>> from radiant_mlhub import Dataset
    >>> for dataset in Dataset.list():
    ...     print(f'{dataset.id}: {dataset.title}')
    'bigearthnet_v1: BigEarthNet V1'


Fetch a Dataset
+++++++++++++++

You can also fetch a dataset by ID using the :meth:`Dataset.fetch <radiant_mlhub.models.Dataset.fetch>` method. This method returns a
:class:`~radiant_mlhub.models.Dataset` instance.

.. code-block:: python

    >>> dataset = Dataset.fetch('bigearthnet_v1')
    >>> print(f'{dataset.id}: {dataset.title}')
    'bigearthnet_v1: BigEarthNet V1'

Work with Dataset Collections
+++++++++++++++++++++++++++++

Datasets have 1 or more collections associated with them. Collections fall into 2 types:

* ``source_imagery``: Collections of source imagery associated with the dataset
* ``labels``: Collections of labeled data associated with the dataset (these collections implement the
  `STAC Label Extension <https://github.com/radiantearth/stac-spec/tree/master/extensions/label>`_)

To list all the collections associated with a dataset use the :attr:`~radiant_mlhub.models.Dataset.collections` attribute.

.. code-block:: python

    >>> dataset.collections
    [<Collection id=bigearthnet_v1_source>, <Collection id=bigearthnet_v1_labels>]
    >>> type(dataset.collections[0])
    <class 'radiant_mlhub.models.Collection'>

You can also list the collections by type using the ``collections.source_imagery`` and ``collections.labels`` properties

.. code-block:: python

    >>> from pprint import pprint
    >>> len(dataset.collections.source_imagery)
    1
    >>> source_collection = dataset.collections.source_imagery[0]
    >>> pprint(source_collection.to_dict())
    {'description': 'BigEarthNet v1.0',
     'extent': {'spatial': {'bbox': [[-9.00023345437725,
                                      1.7542686833884724,
                                      83.44558248555553,
                                      68.02168200047284]]},
                'temporal': {'interval': [['2017-06-13T10:10:31Z',
                                           '2018-05-29T11:54:01Z']]}},
     'id': 'bigearthnet_v1_source',
     'keywords': [],
     'license': 'CDLA-Permissive-1.0',
     'links': [{'href': 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source',
                'rel': 'self',
                'type': 'application/json'},
               {'href': 'https://api.radiant.earth/mlhub/v1',
                'rel': 'root',
                'type': 'application/json'}],
     'properties': {},
     'providers': [{'name': 'BigEarthNet',
                    'roles': ['processor', 'licensor'],
                    'url': 'https://api.radiant.earth/mlhub/v1/download/dummy-download-key'}],
     'sci:citation': 'G. Sumbul, M. Charfuelan, B. Demir, V. Markl, "BigEarthNet: '
                     'A Large-Scale Benchmark Archive for Remote Sensing Image '
                     'Understanding", IEEE International Geoscience and Remote '
                     'Sensing Symposium, pp. 5901-5904, Yokohama, Japan, 2019.',
     'stac_extensions': ['eo', 'sci'],
     'stac_version': '1.0.0-beta.2',
     'summaries': {},
     'title': None}

Download a Collection Archive
+++++++++++++++++++++++++++++

You can download all the assets associated with a collection using the :meth:`Collection.download <radiant_mlhub.models.Collection.download>`
method. This method takes a path to a directory on the local file system where the archive should be saved.

If a file of the same name already exists, the client will check whether the downloaded file is complete by comparing its size against the
size of the remote file. If they are the same size, the download is skipped, otherwise the download will be resumed from the point where it
stopped. You can control this behavior using the ``if_exists`` argument. Setting this to ``"skip"`` will skip the download for existing
files *without* checking for completeness (a bit faster since it doesn't require a network request), and setting this to ``"overwrite"``
will overwrite any existing file.

.. code-block:: python

    >>> source_collection.download('~/Downloads')
    28%|██▊       | 985.0/3496.9 [00:35<00:51, 48.31M/s]

Collection archives are gzipped tarballs. You can read more about the structure of these archives in `this Medium post
<https://medium.com/radiant-earth-insights/archived-training-dataset-downloads-now-available-on-radiant-mlhub-7eb67daf094e>`_.
