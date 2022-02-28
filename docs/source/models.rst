ML Models
=========

A **Model** represents a STAC Item implementing the `ML Model extension <https://github.com/stac-extensions/ml-model/>`_.
The goal of the ML Model Extension is to provide a way of cataloging machine learning (ML) models that operate on
Earth observation (EO) data described as a STAC catalog.

To discover and fetch models you can either use the low-level client methods from :mod:`radiant_mlhub.client` or the
:class:`~radiant_mlhub.models.MLModel` class. Using the :class:`~radiant_mlhub.models.MLModel` class is the recommended
approach, but both methods are described below.

Discovering Models
++++++++++++++++++

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
    'model-cyclone-wind-estimation-torchgeo-v1'
    >>> first_model['properties'].keys()
    dict_keys(['title', 'license', 'sci:doi', 'datetime', 'providers', 'description', 'end_datetime', 'sci:citation', 'ml-model:type', 'start_datetime', 'sci:publications', 'ml-model:architecture', 'ml-model:prediction_type', 'ml-model:learning_approach'])

You can also discover models using the :meth:`MLModel.list <radiant_mlhub.models.MLModel.list>` method. This is the recommended way of
listing models. This method returns a list of :class:`MLModel <radiant_mlhub.models.MLModel>` instances.

.. code-block:: python

    >>> from radiant_mlhub import MLModel
    >>> from pprint import pprint
    >>> models = MLModel.list()
    >>> first_model = models[0]
    >>> first_model.id
    'model-cyclone-wind-estimation-torchgeo-v1'
    >>> pprint(first_model.assets)
    {'inferencing-checkpoint': <Asset href=https://zenodo.org/record/5773331/files/last.ckpt?download=1>,
     'inferencing-compose': <Asset href=https://raw.githubusercontent.com/RadiantMLHub/cyclone-model-torchgeo/main/inferencing.yml>}
    >>> len(first_model.links)
    7
    >>> # print only the ml-model and mlhub related links
    >>> pprint([ link for link in first_model.links if 'ml-model:' in link.rel or 'mlhub:' in link.rel])
    [<Link rel=ml-model:inferencing-image target=docker://docker.io/radiantearth/cyclone-model-torchgeo:1>,
     <Link rel=ml-model:train-data target=https://api.radiant.earth/mlhub/v1/collections/nasa_tropical_storm_competition_train_source>,
     <Link rel=mlhub:training-dataset target=https://mlhub.earth/data/nasa_tropical_storm_competition>]
    >>> # you can access rest of properties as a dict
    >>> first_model.properties.keys()
    dict_keys(['title', 'license', 'sci:doi', 'datetime', 'providers', 'description', 'end_datetime', 'sci:citation', 'ml-model:type', 'start_datetime', 'sci:publications', 'ml-model:architecture', 'ml-model:prediction_type', 'ml-model:learning_approach'])
 
Fetching a Model
++++++++++++++++

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
    7

See the Discovering Models section above for more Python example code.