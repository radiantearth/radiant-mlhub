# 1. Record architecture decisions

Date: 2020-12-17

## Status

Accepted

## Context

We need to record the architectural decisions made on this project.

## Decision

We will use a modified version of Architecture Decision Records, as [described by Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions). ADR documents that are specific to this project will be stored in the `docs/adr` directory within this repository. Instead of using the "deprecated" and "superseded" status value, we will move ADRs that are no longer applicable into the `docs/adr/archive` directory in this repository.

## Consequences

See Michael Nygard's article, linked above, for general consequences related to using ADR documents. For a lightweight ADR toolset, see Nat Pryce's [adr-tools](https://github.com/npryce/adr-tools).

Moving deprecated and/or superseded decisions into a separate directory will meant that developers can see all currently relevant decisions in a single place, but will need to navigate to a separate location to see the full history of architectural decisions.
