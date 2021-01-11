# 3. Will not implement get_items

Date: 2021-01-11

## Status

Accepted

## Context

The Radiant MLHub API implements the `/items` endpoint as described in the [STAC API - Features](https://github.com/radiantearth/stac-api-spec/tree/master/ogcapi-features) 
documentation for retrieving the STAC Items associated with a given Collection. Since this is a paginated endpoint with an opaque next token, 
pages of items must be retrieved sequentially. For very large datasets and collections, this means that retrieving all items in a collection 
may require hundreds or thousands of API requests and can be very slow. Additionally, the spec does not provide a mechanism for determining the 
total number of items in a collection, which precludes us from showing overall progress when looping over or retrieving items.

## Decision

To avoid a confusing user experience when working with Items, and to avoid inadvertently swamping the API with requests, we will not provide 
a method in either the low-level client or on the `Collection` classes to loop over the items in a collection. Preliminary work had adapted 
the [`Collection.get_items`](https://pystac.readthedocs.io/en/latest/api.html#pystac.Catalog.get_items) method to make paginated requests to 
the `/items` endpoint. Instead, this method will raise a `NotImplementedError` to indicate that this feature is not available. 

*Work is planned to add an endpoint to the Radiant MLHub API to enable downloading a single archive containing all items associated with a 
Collection. Support for this endpoint in the Python client may be the subject of a separate ADR.* 

## Consequences

Users may still make requests directly to the `/items` endpoint using the `Session.paginate` method, but they will not have a convenient 
method for working with Items associated with a Collection as PySTAC objects.


