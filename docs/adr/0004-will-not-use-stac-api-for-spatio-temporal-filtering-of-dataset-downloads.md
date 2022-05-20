# 4. Will not use stac-api for spatio-temporal filtering of dataset downloads.

Date: 2022-04-27

## Status

Accepted

## Context

The updated `Dataset.download` feature will offer spatio-temporal
filtering as well as collection and band filtering.

## Decision

The filtering will be performed client side in Python, rather than
using our stac-api.

## Consequences

This is a workaround for our stac-api not really being optimal or well
aligned with our use case of large datasets with millions of small
chip items.
