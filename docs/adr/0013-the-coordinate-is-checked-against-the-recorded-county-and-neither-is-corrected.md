# 13. The coordinate is checked against the recorded county, and neither is corrected

Date: 2026-08-23

## Status

Accepted. Extends ADR 0009, which reports CAL FIRE's `COUNTY` field as published.

## Context

ADR 0009 added the publisher's county to the retrieval so the overlap could be cut by
county, and refused to correct it: where a record's coordinate and its recorded county
disagree, correcting it would be a second opinion about where a structure is. The
refusal left a question open that a reader asks immediately: how often do they
disagree at all?

That question is answerable without adjudicating. An authoritative boundary layer
exists: California County Boundaries and Identifiers, published by the California
Department of Technology on data.ca.gov, whose own metadata warns that "boundary
accuracy is *not* guaranteed ... errors will exist." A point-in-polygon test against
it produces a second opinion that can be counted against the first.

## Decision

Every record with both a usable coordinate and a county label the layer carries is
compared once:

- **agreed**: the coordinate falls inside the polygon carrying that name;
- **disagreed**: the coordinate falls inside some other county's polygon;
- **matched no county**: the coordinate falls inside none of them.

Records whose label the layer does not carry are counted separately as unmatchable,
never guessed at. Records without a usable coordinate or without a county stay in
every other denominator here and none in this one.

The comparison is published as counts with denominators and Wilson intervals, overall
and per recorded county in name order. Nothing is corrected, moved, re-attributed, or
dropped: the COUNTY field keeps its value everywhere else in this project, and this
block says how often two published sources answer one question differently.

## Consequences

The project gains a fourth source and a ninth fetched field's worth of honesty about
the eighth. The per-county cut of ADR 0009 keeps its shape; the disagreement counts
sit beside it and change nothing about it. Where the disagreement share is high, the
publisher's warning supplies the reading: generalized boundaries produce edge
mismatches, and only a count can be published about them without pretending to know
which source is right.
