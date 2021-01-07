# 2. Resolving API key

Date: 2020-12-17

## Status

Accepted

## Context

We need a convenient system for managing API keys used by the Python client. This system should give the user multiple options for 
providing an API key to be used when making a request to the API. These options should include:

* Storing API keys on the users system
* Reading an API key from the environment
* Passing an API key directly to the API request methods

Users may have multiple valid API keys associated with their account at any given time. The system for storing API keys on the user's 
system must accommodate this and provide a clear, deterministic way of resolving an API key for a given project.

We anticipate the need to store other data related to Radiant MLHub for uses unrelated to authentication. For instance, we may have a need to 
track the progress of downloads so that they can be resumed if interrupted, or we may want to specify a base URL in a config file so that 
developers can test against the staging environment. The method that we choose for storing API keys on the user's system must not preclude 
us from storing this additional information. 

## Decision

The Python client will resolve the API key to be used in a request in the following order:

1) Passing an `api_key` argument directly to the method
2) Setting an `MLHUB_API_KEY` environment variable
3) Passing a `profile` argument directly to the method. This will read the API key from the given profile (see below for details)
4) Setting an `MLHUB_PROFILE` environment variable. This will read the API key from the given profile (see below for details)
5) Using the API from the `default` profile

Profiles will be stored in a `.mlhub/profiles` file in the user's home directory. This file will be an INI file containing at least a 
`[default]` section with an `api_key` value. The file may contain other sections corresponding to named profiles. Any `profile` argument 
passed to a method must correspond to one of these section names, or it will raise an exception.

## Consequences

If the user has a single API key, they will be able to save it in a `default` profile in a `.mlhub/profiles` file in their user directory 
and all projects that access the API will use that key. If the user have a need for project-specific API keys, they can specify those in 
other named profiles (e.g. `some-project`), in the same `.mlhub/profiles` file. If the user needs finer-grained control over the API key 
being used, they can specify it as an environment variable or as an argument to the request method.

Users will need knowledge or guidance on the syntax used in the `.mlhub/profiles` file in order to configure it correctly. They 
will also need guidance on how to generate and/or find their API key outside the Python client.

Using an INI file means that we can use the `configparser` module from the Python standard library, removing the need for an additional 
dependency like (e.g. `toml`). Additional configuration (e.g. base URL) can be added to the config file and additional files can be written 
to the `.mlhub` directory without affecting the authentication flow.