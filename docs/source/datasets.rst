Datasets
========

A **dataset** represents a group of 1 or more related STAC Collections. They group together any source imagery Collections with the associated
label Collections to provide a convenient mechanism for accessing all of these data together. For instance, the ``bigearthnet_v1_source``
Collection contains the source imagery for the `BigEarthNet <http://bigearth.net/>`_ training dataset and, likewise, the
``bigearthnet_v1_labels`` Collection contains the annotations for that same dataset. These 2 collections are grouped together into the
``bigearthnet_v1`` dataset.

The `Radiant MLHub Training Data Registry <http://registry.mlhub.earth/>`_ provides an overview of the datasets available through the
Radiant MLHub API along with dataset metadata and a listing of the associated Collections.

To discover and fetch datasets you can either use the low-level client methods from :mod:`radiant_mlhub.client` or the
:class:`~radiant_mlhub.models.Dataset` class. Using the :class:`~radiant_mlhub.models.Dataset` class is the recommended approach, but
both methods are described below.

.. note::

    The objects returned by the Radiant MLHub API dataset endpoints are not STAC-compliant objects and therefore the :class:`Dataset`
    class described below is not a :doc:`PySTAC <pystac:index>` object.

Discovering Datasets
++++++++++++++++++++

The Radiant MLHub ``/datasets`` endpoint returns a list of objects describing the available datasets and their associated collections. You
can use the low-level :func:`~radiant_mlhub.client.list_datasets` function to work with these responses as native Python data types
(:class:`list` and :class:`dict`). This function is a generator that yields a :class:`dict` for each dataset.

.. code-block:: python

    >>> from radiant_mlhub.client import list_datasets
    >>> from pprint import pprint
    >>> datasets = list_datasets()
    >>> first_dataset = datasets[0]
    >>> pprint(first_dataset)
    {'collections': [{'id': 'bigearthnet_v1_source', 'types': ['source_imagery']},
                 {'id': 'bigearthnet_v1_labels', 'types': ['labels']}],
     'id': 'bigearthnet_v1',
     'title': 'BigEarthNet V1'}

You can also discover datasets using the :meth:`Dataset.list <radiant_mlhub.models.Dataset.list>` method. This is the recommended way of
listing datasets. This method returns a list of :class:`Dataset <radiant_mlhub.models.Dataset>` instances.

.. code-block:: python

    >>> from radiant_mlhub import Dataset
    >>> datasets = Dataset.list()
    >>> first_dataset = datasets[0]
    >>> first_dataset.id
    'bigearthnet_v1'
    >>> first_dataset.title
    'BigEarthNet V1'

Fetching a Dataset
++++++++++++++++++

The Radiant MLHub ``/datasets/{dataset_id}`` endpoint returns an object representing a single dataset. You can use the low-level
:func:`~radiant_mlhub.client.get_dataset` function to work with this response as a :class:`dict`.

.. code-block:: python

    >>> from radiant_mlhub.client import get_dataset_by_id
    >>> dataset = get_dataset_by_id('bigearthnet_v1')
    >>> pprint(dataset)
    {'collections': [{'id': 'bigearthnet_v1_source', 'types': ['source_imagery']},
                 {'id': 'bigearthnet_v1_labels', 'types': ['labels']}],
     'id': 'bigearthnet_v1',
     'title': 'BigEarthNet V1'}

You can also fetch a dataset from the Radiant MLHub API based on the dataset ID using the :meth:`Dataset.fetch <radiant_mlhub.models.Dataset.fetch>`
method. This is the recommended way of fetching a dataset. This method returns a :class:`~radiant_mlhub.models.Dataset` instance.

.. code-block:: python

    >>> dataset = Dataset.fetch_by_id('bigearthnet_v1')
    >>> dataset.id
    'bigearthnet_v1'

If you would rather fetch the dataset using its `DOI <https://www.doi.org/>`__ you can do so as
well:

.. code-block:: python

    >>> from radiant_mlhub.client import get_dataset_by_doi
    >>> # Using the client...
    >>> dataset = get_dataset_by_doi("10.6084/m9.figshare.12047478.v2")
    >>> # Using the model classes...
    >>> dataset = Dataset.fetch_by_doi

You can also use the more general :func:`~radiant_mlhub.client.get_dataset` and :meth:`Dataset.fetch
<radiant_mlhub.models.Dataset.fetch>` methods to get a dataset using either method:

.. code-block:: python

    >>> from radiant_mlhub.client import get_dataset
    >>> # These will all return the same dataset
    >>> dataset = get_dataset("ref_african_crops_kenya_02")
    >>> dataset = get_dataset("10.6084/m9.figshare.12047478.v2")
    >>> dataset = Dataset.fetch("ref_african_crops_kenya_02")
    >>> dataset = Dataset.fetch("10.6084/m9.figshare.12047478.v2")

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
    'bigearthnet_v1_source'
    >>> len(first_dataset.collections.labels)
    1
    >>> first_dataset.collections.labels[0].id
    'bigearthnet_v1_labels'

.. warning::

    There are rare cases of collections that contain both ``source_imagery`` and ``labels`` items (e.g. the SpaceNet collections). In these cases, the
    collection will be listed in both the ``dataset.collections.labels`` and ``dataset.collections.source_imagery`` lists, but *will only appear once
    in the main ``dataset.collections`` list*. This may cause what appears to be a mismatch in list lengths:

    .. code-block:: python

        >>> len(dataset.collections.source_imagery) + len(dataset.collections.labels) == len(dataset.collections)
        False

.. note::

    Both the low-level client functions and the class methods also accept keyword arguments that are passed directly to
    :func:`~radiant_mlhub.session.get_session` to create a session. See the :ref:`Authentication` documentation for details on how to
    use these arguments or configure the client to read your API key automatically.

Downloading a Dataset
++++++++++++++++++++++++

The Radiant MLHub ``/archive/{archive_id}`` endpoint allows you to download an archive of all assets associated with a given collection.
The :meth:`Dataset.download <radiant_mlhub.models.Dataset.download>` method provides a convenient way of using this endpoint to download
the archives for all collections associated with a given dataset. This method downloads the archives for all associated collections
into the given output directory and returns a list of the paths to these archives.

If a file of the same name already exists for any of the archives, this method will check whether the downloaded file is complete by
comparing its size against the size of the remote file. If they are the same size, the download is skipped, otherwise the download
will be resumed from the point where it stopped. You can control this behavior using the ``if_exists`` argument. Setting this to
``"skip"`` will skip the download for existing files *without* checking for completeness (a bit faster since it doesn't require a
network request), and setting this to ``"overwrite"`` will overwrite any existing file.


.. code-block:: python

    >>> dataset = Collection.fetch('bigearthnet_v1')
    >>> archive_paths = dataset.download('~/Downloads')
    >>> len(archive_paths)
    2

To check the total size of the download archives for all collections in the dataset without actually
downloading it, you can use the :attr:`Dataset.total_archive_size` property.

.. code-block:: python

    >>> dataset.total_archive_size
    71311240007

Collection archives are gzipped tarballs. You can read more about the structure of these archives in `this Medium post
<https://medium.com/radiant-earth-insights/archived-training-dataset-downloads-now-available-on-radiant-mlhub-7eb67daf094e>`_.
