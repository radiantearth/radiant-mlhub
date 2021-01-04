Getting Started
===============

This guide will walk you through the basic usage of the ``radiant_mlhub`` library, including:

* Installing the library
* Configuring the library
* Making authenticated API requests

Installation
++++++++++++

.. code-block:: console

    $ pip install radiant_mlhub

Configuration
+++++++++++++

If you have not done so already, you will need to register for an MLHub API key `here <http://dashboard.mlhub.earth/>`_.

Once you have your API key, you will need to create a default profile by setting up a ``.mlhub/profiles`` file in your home directory:

.. code-block:: console

    $ mkdir -p ~/.mlhub
    $ touch ~/.mlhub/profiles

Open ``~/.mlhub/profiles`` in a text editor and add the following content:

.. code-block:: ini

    [default]
    api_key = <your_api_key_here>

Making API Requests
+++++++++++++++++++

Once you have your ``profiles`` file in place, you can create a session that will be used to make authenticated requests to the API:

.. code-block:: python

    >>> from radiant_mlhub import get_session
    >>> session = get_session()

You can use this session to make authenticated calls to the API. For example, to list all collections:

.. code-block:: python

    >>> r = session.get('/collections')  # Leading slash is optional
    >>> collections = r.json()['collections']
    >>> print(len(collections))
    47

For details on more fine-grained control over which API key is used for a session, see the :ref:`Authentication` documentation.

Discover Collections
++++++++++++++++++++

You can use the :meth:`Collection.list <radiant_mlhub.models.Collection.list>` method to list all of the collections available in MLHub. This method returns
a generator that yields :class:`~radiant_mlhub.models.Collection` instances. You can use the properties of these instances to get more
information about each collection. For instance, the following code will print the ID and description for each collection:

.. code-block:: python

    >>> from radiant_mlhub import Collection
    >>> for collection in Collection.list():
    ...     print(f'{collection.id}: {collection.description}')

    ref_african_crops_kenya_01_labels: African Crops Kenya
    ref_african_crops_kenya_01_source: African Crops Kenya Source Imagery
    ref_african_crops_tanzania_01_labels: African Crops Tanzania
    ref_african_crops_tanzania_01_source: African Crops Tanzania Source Imagery
    ref_african_crops_uganda_01_labels: African Crops Uganda
    ref_african_crops_uganda_01_source: African Crops Uganda Source Imagery
    microsoft_chesapeake_landsat_leaf_off: Microsoft Chesapeake Landsat 8 Leaf-Off Composite
    ...

Get Collection
++++++++++++++

If you know the ID of a collection, you can fetch it from the MLHub API using the :meth:`Collection.fetch <radiant_mlhub.models.Collection.fetch>` class
method:

.. code-block:: python

    >>> from pprint import pprint
    >>> collection = Collection.fetch('bigearthnet_v1_source')
    >>> print(collection)
    <Collection id=bigearthnet_v1_source>
    >>> pprint(collection.to_dict())
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
                    'url': 'https://api.radiant.earth/mlhub/v1/download/gAAAAABf6lIUqtKGKItY35ACBtk0FSOZwOjQERPHKo8cp5h0S50GkpGQN-lOq-itFvBAxwt9oBE4a71pZu9Sd3eM44mz8ezjSyrH02SjiVKfGREiGD2rJjHsjkv1TuBh36M4RptF5S7zlt3k5BRi3EaO3uaWvM-5IFwT5YklrGlpOWIkeKcfVSqTgNiqg2jL-t89x-Yxjz3rSJOltq6unUlEMkImzp0MnW1YlALq4Wf2TdHPBOdZIUk='}],
     'sci:citation': 'G. Sumbul, M. Charfuelan, B. Demir, V. Markl, "BigEarthNet: '
                     'A Large-Scale Benchmark Archive for Remote Sensing Image '
                     'Understanding", IEEE International Geoscience and Remote '
                     'Sensing Symposium, pp. 5901-5904, Yokohama, Japan, 2019.',
     'stac_extensions': ['eo', 'sci'],
     'stac_version': '1.0.0-beta.2',
     'summaries': {},
     'title': None}

Get Items
+++++++++

Once you have a collection you can loop over the items for that collection using the :meth:`~radiant_mlhub.models.Collection.get_items` method.
This method returns a generator that yields :class:`pystac.Item` instances.

.. code-block:: python

    >>> items = collection.get_items()
    >>> first_item = next(items)
    >>> pprint(first_item.to_dict())
    # NOTE: Some of the output has been truncated to save space
    {'assets': {'B01': {'eo:bands': [{'common_name': 'Coastal Aerosol',
                                  'description': 'Coastal Aerosol',
                                  'name': 'B01'}],
                    'href': 'https://api.radiant.earth/mlhub/v1/download/gAAAAABf61GeAzydef_dWJNEYP8d0crimCkAcg5KVSzH9qEI2V294tzHdbp1hrMqZnx1Gx17Y7SVwnqqJNv8XZzCwPFYAMKxZGEEu-rZER7PjM7oTYVq5NwTV0pwHT9BB7b-eP4OHH8KOlB3StVlZXCHPnpFBadKvWgCyoYvVGML1vDYCXB8A5Ai56it7uRgdVQkGmRMqdcl_WFVt6BWGDGRqqhTCCsnxVoEzNFZe9d-Ta21hOxyG4KS0o8SBBsBjK3zNa0t8JgXoy1yn-pa2SfxpH_Zn-2xBS8KZbCuYbAtBTDXxgJK8IhdwPIaWudNarKWVw90v8W2ZO3jf9ypP-oh_HfUWHQ4AVwjiJGgVRoaqcQ_Gr5sF7aQTa6vQLpR7PkV_CJ3yUeM',
                    'roles': [],
                    'title': 'S2A_MSIL2A_20180526T100031_65_62_B01',
                    'type': 'image/tiff; application=geotiff; '
                            'profile=cloud-optimized'},
            ...
            'B8A': {'eo:bands': [{'common_name': 'Narrow NIR',
                                  'description': 'Narrow NIR',
                                  'name': 'B8A'}],
                    'href': 'https://api.radiant.earth/mlhub/v1/download/gAAAAABf61GeeN7HJveXRngndybyuoN-wUIk0YjDpLhYR7xDM_F2qjBlfHCS4UMvmZMX3JbDuZTVq-JkTmlE8JhotqHCVrXskF1DVTVOHiCmiI66Crd0XrXOO_zGRbPRcNyF4t3MY1K-BojV4xPSGNo7XPGNauPCRhtJMmNpRlp-OZ6X35M--QpUjkrRDfcU2_y1JtepiMxvcmZkpr54xIMPJAdTPs0P10zOL7-eLdoymK4AU6imdsnMxxio9T36FxPteilmRCDv903ox2Hu_qqcq2XHxJSzGEu9-mzZtfrj3BzwWR_cdIWD4IHDvc_VRbQMFyO-rNC7_JFw-JD0sbT-M64M1BC9-W7jxjb6AUqOYe7uIrU9Yce_wuTcnOHQD4flZoxak8hQ',
                    'roles': [],
                    'title': 'S2A_MSIL2A_20180526T100031_65_62_B8A',
                    'type': 'image/tiff; application=geotiff; '
                            'profile=cloud-optimized'}},
     'bbox': [24.922484743531783,
              3.750132313031408,
              73.2472583535805,
              66.00142153578817],
     'collection': 'bigearthnet_v1_source',
     'geometry': {'coordinates': [[[24.92413706459548, 66.00142153578817],
                                   [24.950515309783018, 66.00074619651735],
                                   [73.2472583535805, 3.750132313031408],
                                   [24.922484743531783, 65.99068084445847],
                                   [24.92413706459548, 66.00142153578817]]],
                  'type': 'Polygon'},
     'id': 'bigearthnet_v1_source_S2A_MSIL2A_20180526T100031_65_62',
     'links': [{'href': 'https://api.radiant.earth/mlhub/v1/collections/bigearthnet_v1_source',
                'rel': 'parent',
                'title': 'Parent collection',
                'type': 'application/json'}],
     'properties': {'constellation': 'Sentinel-2',
                    'datetime': '2018-05-26T10:00:31Z',
                    'eo:bands': [{'common_name': 'Coastal Aerosol',
                                  'description': 'Coastal Aerosol',
                                  'name': 'B01'},
                                 ...
                                 {'common_name': 'SWIR',
                                  'description': 'SWIR (2202.4nm)',
                                  'name': 'B12'}],
                    'gsd': 30,
                    'instruments': ['MSI'],
                    'platform': 'Sentinel-2',
                    'validation:attemptedExtensions': ['eo'],
                    'validation:errors': []},
     'stac_extensions': ['eo'],
     'stac_version': '1.0.0-beta.2',
     'type': 'Feature'}