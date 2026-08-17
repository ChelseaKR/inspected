# 5. An invalid published polygon is repaired, and the repair is measured

Date: 2026-08-17

## Status

Accepted.

## Context

Eight of the 59 outlines fail an OGC validity check on retrieval, with ring
self-intersections and nested shells. Two of the eight are the two largest territories in
the state, so this is not an edge case.

Shapely answers a containment question about an invalid polygon. The answer is undefined,
not wrong in a detectable way. Three options:

1. Use them as they arrive. Undefined answers for most of the record set.
2. Refuse them. Removes the two territories holding the large majority of the records, so
   the project measures almost nothing.
3. Repair them, and publish how much rests on the repair.

An earlier draft used `buffer(0)` and a later one used `make_valid`. The two disagreed on
roughly 770 placements, which is the measure of how real this choice is.

## Decision

Repair with `make_valid`, keep only the polygonal result, record the repair on each
territory row, name the repaired territories in the report, and publish the share of the
placed total that sits inside a repaired polygon. A repair producing nothing polygonal
removes the territory from the index and is reported as unusable, never as a territory
holding zero records.

## Consequences

91.7% of placed records sit inside a repaired polygon. That number is prominent in the
README rather than buried, because it is the largest single caveat on the result.

The sensitivity is measured only in the sense that the exposure is sized. Running two
repair strategies against each other and publishing the delta is not done, and the README
says so.
