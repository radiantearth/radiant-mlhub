# 5. Add shapely as python dependency.

Date: 2022-04-27

## Status

Accepted

## Context

In Dataset.download() we are performing client side spatio-temporal
filtering and other filtering options. Adding a spatial index and
search tool is therefore required.

Relates to:

* [0004-will-not-use-stac-api-for-spatio-temporal-filtering-of-dataset-downloads.md](Will not use stac-api for spatio-temporal filtering of dataset
  downloads.)
* https://radiantearth.atlassian.net/browse/ME-1140

## Decision

Add `shapely` to Python dependencies.

## Consequences

The `radiant_mlhub` client gets another Python dependency. This is an
accepted trade-off.
