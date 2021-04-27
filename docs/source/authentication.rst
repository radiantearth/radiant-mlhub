Authentication
==============

The Radiant MLHub API uses API keys to authenticate users. These keys must be passed as a ``key`` query parameter in any request made to the API.
Anyone can register for an API key by going to `https://dashboard.mlhub.earth <https://dashboard.mlhub.earth>`_ and creating an account.
Once you have logged into your account, go to `http://dashboard.mlhub.earth/api-keys <http://dashboard.mlhub.earth/api-keys>`_ to create
API keys.

Using API Keys
++++++++++++++

The best way to add your API key to requests is to create a :class:`~radiant_mlhub.session.Session` instance using the
:func:`~radiant_mlhub.session.get_session` helper function and making requests using this instance:

.. code-block:: python

    >>> from radiant_mlhub import get_session
    >>> session = get_session()
    >>> r = session.get(...)

You can associate an API key with a session in a number of ways:

* programmatically via an instantiation argument
* using environment variables
* using a named profile

The :class:`~radiant_mlhub.session.Session` resolves an API key by trying each of the following (in this order):

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

*If none of the above strategies results in a valid API key, then an* :exc:`~radiant_mlhub.exceptions.APIKeyNotFound` *exception is raised.*

The :class:`radiant_mlhub.session.Session` instance inherits from :class:`requests.Session` and adds a few conveniences to a typical
session:

* Adds the API key as a ``key`` query parameter
* Adds an ``Accept: application/json`` header
* Adds a ``User-Agent`` header that contains the package name and version, plus basic system information like the the OS name
* Prepends the MLHub root URL (``https://api.radiant.earth/mlhub/v1/``) to any request paths without a domain
* Raises a :exc:`radiant_mlhub.exceptions.AuthenticationError` for ``401 (UNAUTHORIZED)`` responses

Using Profiles
++++++++++++++

Profiles in ``radiant_mlhub`` are inspired by the `Named Profiles <https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html>`_
used by ``boto3`` and ``awscli``. These named profiles provide a way to store API keys (and potentially other configuration) on your local system
so that you do not need to explicitly set environment variables or pass in arguments every time you create a session.

All profile configuration must be stored in a ``.mlhub/profiles`` file in your home directory. The ``profiles`` file uses the INI file
structure supported by Python's ``configparser`` module `as described here <https://docs.python.org/3/library/configparser.html#supported-ini-file-structure>`_.

.. hint::

    If you do not have write access to the home directory on your machine, you can change the location of the ``profiles`` file using the ``MLHUB_HOME``
    environment variables. For instance, setting ``MLHUB_HOME=/tmp/some-directory/.mlhub`` will cause the client to look for your profiles in a
    ``/tmp/some-directory/.mlhub/profiles`` file. You may want to permanently set this environment variable to ensure the client continues to look in
    the correct place for your profiles.

The easiest way to configure a profile is using the ``mlhub configure`` CLI tool documented in the :ref:`CLI Tools section<CLI Tools>`:

.. code-block:: console

    $ mlhub configure
    API Key: <Enter your API key when prompted>
    Wrote profile to /Users/youruser/.mlhub/profiles

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

Relative v. Absolute URLs
-------------------------

Any URLs that do not include a scheme (``http://``, ``https://``) are assumed to be relative to the Radiant MLHub root URL. For instance,
the following code would make a request to ``https://api.radiant.earth/mlhub/v1/some-endpoint``:

.. code-block:: python

    >>> session.get('some-endpoint')

but the following code would make a request to ``https://www.google.com``:

.. code-block:: python

    >>> session.get('https://www.google.com')

It is not recommended to make calls to APIs other than the Radiant MLHub API using these sessions.