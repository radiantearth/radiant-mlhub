Authentication
==============

The MLHub API uses API keys to authenticate users. These keys must be passed as a `key` query parameter in any request made to the API.
Anyone can register for an API key by going to `https://dashboard.mlhub.earth <https://dashboard.mlhub.earth>`_ and creating an account.
Once you have logged into your account, go to `http://dashboard.mlhub.earth/api-keys <http://dashboard.mlhub.earth/api-keys>`_ to create
API keys.

Using API Keys
++++++++++++++

The best way to add your API key to requests is to create :class:`~radiant_mlhub.client.Session` instance using
:func:`radiant_mlhub.get_session` and making requests using this instance:

.. code-block:: python

    >>> from radiant_mlhub import get_session
    >>> session = get_session()
    >>> r = session.get(...)

You can associated an API key with a session in a number of ways: programmatically via an instantiation argument, using environment
variables, or using a named profile. The :class:`~radiant_mlhub.client.Session` resolves an API key by trying each of the following, in
order:

1) Use an ``api_key`` argument provided during instantiation

   .. code-block:: python

        >>> session = get_session(api_key='myapikey)

2) Use an ``MLHUB_API_KEY`` environment variable

   .. code-block:: python

       >>> import os
       >>> os.environ['MLHUB_API_KEY'] = 'myapikey'
       >>> session = get_session()

3) Use a ``profile`` argument provided during instantiation (see :ref:`Using Profiles` section for details)

   .. code-block:: python

       >>> session = get_session(profile='my-profile')

4) Use an ``MLHUB_PROFILE`` environment variable (see :ref:`Using Profiles` section for details)

   .. code-block:: python

       >>> os.environ['MLHUB_PROFILE'] = 'my-profile'
       >>> session = get_session()

5) Use the ``default`` profile (see :ref:`Using Profiles` section for details)

   .. code-block:: python

       >>> session = get_session()

*If none of the above strategies results in a valid API key, then an exception is raised.*

The :class:`radiant_mlhub.client.Session` instance inherits from :class:`requests.Session` and adds 2 conveniences to a typical session:

1) Injects API key into query params
2) Prepends the MLHub root URL (``https://api.radiant.earth/mlhub/v1/``) to request paths

Using Profiles
++++++++++++++

Profiles in ``radiant_mlhub`` are inspired by the `Named Profiles <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`_
used by ``boto3`` and ``awscli``. These named profiles provide a way to store API keys (and potentially other configuration) on your local system
so that you do not need to explicitly set environment variables or pass in arguments every time you create a session.

All profile configuration must be stored in a ``.mlhub/profiles`` file in your home directory. The ``profiles`` file uses the INI file
structure supported by Python's ``configparser`` module `as described here <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_.

Given the following ``profiles`` file...

.. code-block:: ini

    [default]
    api_key = default_api_key

    [project1]
    api_key = some_other_api_key

    [project2]
    api_key = yet_another_api_key

These would be the API keys used by sessions created using the various methods described in :ref:`Using API Keys`:

.. code-block:: python

    # As long as we haven't set the MLHUB_API_KEY or MLHUB_PROFILE environment variables
    #  this will pull from the default profile
    >>> session = get_session()
    >>> session.params['key']
    'default_api_key'

    # Setting the MLHUB_PROFILE environment variable overrides the default profile
    >>> os.environ['MLHUB_PROFILE'] = 'project1'
    >>> session = get_session()
    >>> session.params['key']
    'some_other_api_key'

    # Passing the profile argument directly overrides the MLHUB_PROFILE environment variable
    >>> session = get_session(profile='profile2')
    >>> session.params['key']
    'yet_another_api_key'

    # Setting the MLHUB_API_KEY environment variable overrides any profile-related arguments
    >>> os.environ['MLHUB_API_KEY'] = 'environment_direct'
    >>> session = get_session()
    >>> session.params['key']
    'environment_direct'

    # Passing the api_key argument overrides all other strategies or finding the key
    >>> session = get_session(api_key='argument_direct')
    >>> session.params['key']
    'argument_direct'
