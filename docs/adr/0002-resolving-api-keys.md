# 2. Resolving API key

Date: 2020-12-17

## Status

Proposed

## Context

We need a convenient system for managing API keys used by the Python client. This system should give the user multiple options for providing an API key to be used when making a request to the API. These options should include:

* Storing API keys on the users system
* Reading an API key from the environment
* Passing an API key directly to the API request methods

Users may have multiple valid API keys associated with their account at any given time. The system for storing API keys on the users system must accomodate this and provide a clear, determistic way of resolving an API key for a given project.

We anticipate the need to store other data related to MLHub for uses unrelated to authentication. For instance, we may have a need to track the progress of downloads so that they can be resumed if interrupted, or we may want to specify a base URL in a config file so that developers can test against the staging environment. The method that we choose for storing API keys on the users system must not preclude us from storing this additional information. 

## Decision

The Python client will resolve the API key to be used in a request in the following order:

1) Passing an `api_key` argument directly to the method
2) Setting an `ML_HUB_API_KEY` environment variable
3) Reading the `auth.api_key` value from a `.mlhub/config.ini` file (relative to the current working directory)
4) Reading the `auth.api_key` value from a `.mlhub/config.ini` file (relative the users's home directory)

## Consequences

If the user has a single API key, they will be able to save it in a `.mlhub/config.ini` file in their user directory and all projects that access the API will use that key. If the user have a need for project-specific API keys, they can specify those in `.mlhub/config.ini` files within their project directories. If the user needs finer-grained control over the API key being used, they can specify it as an environment variable or as an argument to the request method.

Users will need to have knowledge or guidance on the syntax used in the `.mlhub/config.ini` file in order to configure it correctly. They will also need guidance on how to generate and/or find their API key outside of the Python client.

Using a `.ini` file means that we can use the `configparser` module from the Python standard library, removing the need for an additional dependency like (e.g. `toml`). Additional configuration (e.g. base URL) can be added to the config file and additional files can be written to the `.mlhub` directory without affecting the authentication flow.