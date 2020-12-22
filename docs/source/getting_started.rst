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

Once you have your `profiles` file in place, you can create a session that will be used to make authenticated requests to the API:

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
