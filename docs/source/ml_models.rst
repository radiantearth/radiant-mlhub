ML Models
=========

A **Model** represents a STAC Item implementing the `ML Model extension <https://github.com/stac-extensions/ml-model/>`_.
The goal of the ML Model Extension is to provide a way of cataloging machine
learning models that operate on earth observation (EO) data described as a STAC
catalog.

To discover and fetch models you can either use the
:class:`~radiant_mlhub.models.MLModel` class or the low-level client methods
from :mod:`radiant_mlhub.client`. Using the
:class:`~radiant_mlhub.models.MLModel` class is the recommended approach, but
both methods are described below.

.. hint::
    The `Radiant MLHub <https://mlhub.earth/>`_ web application provides an
    overview of all the ML models available through the Radiant
    MLHub API.

Discovering Models
++++++++++++++++++

You can discover models using the :meth:`MLModel.list <radiant_mlhub.models.MLModel.list>` method. This method returns a list of :class:`MLModel <radiant_mlhub.models.MLModel>` instances.

.. code-block:: python

    >>> from radiant_mlhub import MLModel
    >>> models = MLModel.list()
    >>> first_model = models[0]
    >>> for model in models[0:2]:  # print first two models, for example
    >>>     print(model)
    model-crop-detection-torchgeo-v1: A Spatio-Temporal Deep Learning-Based Crop Classification Model for Satellite Imagery
    model-cyclone-wind-estimation-torchgeo-v1: Tropical Cyclone Wind Estimation Model

You can fetch a model by ID using :meth:`MLModel.fetch <radiant_mlhub.models.MLModel.fetch>` method.

.. code-block:: python

    >>> model = MLModel.fetch('model-cyclone-wind-estimation-torchgeo-v1')
    >>> model.assets
    {'inferencing-compose': <Asset href=https://raw.githubusercontent.com/RadiantMLHub/cyclone-model-torchgeo/main/inferencing.yml>,
 'inferencing-checkpoint': <Asset href=https://zenodo.org/record/5773331/files/last.ckpt?download=1>}
    >>> len(first_model.links)
    8
    >>> # print only the ml-model and mlhub related links
    >>> from pprint import pprint
    >>> pprint([ link for link in first_model.links if 'ml-model:' in link.rel or 'mlhub:' in link.rel])
    [<Link rel=ml-model:inferencing-image target=docker://docker.io/radiantearth/crop-detection-dl:1>,
 <Link rel=ml-model:train-data target=https://api.radiant.earth/mlhub/v1/collections/ref_african_crops_kenya_02_source>,
 <Link rel=ml-model:train-data target=https://api.radiant.earth/mlhub/v1/collections/ref_african_crops_kenya_02_labels>,
 <Link rel=mlhub:training-dataset target=https://mlhub.earth/data/ref_african_crops_kenya_02>]
    >>> # you can access rest of properties as a dict
    >>> first_model.properties.keys()
    dict_keys(['title', 'license', 'sci:doi', 'datetime', 'providers', 'description', 'end_datetime', 'sci:citation', 'ml-model:type', 'start_datetime', 'sci:publications', 'ml-model:training-os', 'ml-model:architecture', 'ml-model:prediction_type', 'ml-model:learning_approach', 'ml-model:training-processor-type'])

Low-level Client
----------------

The Radiant MLHub ``/models`` endpoint returns a list of objects describing the available models and their properties. You
can use the low-level :func:`~radiant_mlhub.client.list_models` function to work with these responses as native Python data types
(:class:`list` and :class:`dict`).

.. code-block:: python

    >>> from radiant_mlhub.client import list_models
    >>> models = list_models()
    >>> first_model = models[0]
    >>> first_model.keys()
    dict_keys(['id', 'bbox', 'type', 'links', 'assets', 'geometry', 'collection', 'properties', 'stac_version', 'stac_extensions'])
    >>> first_model['id']
    'model-cv4a-crop-detection-v1'
    >>> first_model['properties'].keys()
    dict_keys(['title', 'license', 'sci:doi', 'datetime', 'providers', 'description', 'end_datetime', 'sci:citation', 'ml-model:type', 'start_datetime', 'sci:publications', 'ml-model:training-os', 'ml-model:architecture', 'ml-model:prediction_type', 'ml-model:learning_approach', 'ml-model:training-processor-type'])

Fetching Model Metadata
+++++++++++++++++++++++

The Radiant MLHub ``/models/{model_id}`` endpoint returns an object representing a single model. You can use the low-level
:func:`~radiant_mlhub.client.get_model_by_id` function to work with this response as a :class:`dict`.

.. code-block:: python

    >>> from radiant_mlhub.client import get_model_by_id
    >>> model = get_model_by_id('model-cyclone-wind-estimation-torchgeo-v1')
    >>> model.keys()
    dict_keys(['id', 'bbox', 'type', 'links', 'assets', 'geometry', 'collection', 'properties', 'stac_version', 'stac_extensions'])

You can also fetch a model from the Radiant MLHub API based on the model ID using the :meth:`MLModel.fetch <radiant_mlhub.models.MLModel.fetch>`
method. This is the recommended way of fetching a model. This method returns a :class:`~radiant_mlhub.models.MLModel` instance.

.. code-block:: python

    >>> from radiant_mlhub import MLModel
    >>> model = MLModel.fetch('model-cyclone-wind-estimation-torchgeo-v1')
    >>> model.id
    'model-cyclone-wind-estimation-torchgeo-v1'
    >>> len(model.assets)
    2
    >>> len(model.links)
    8
