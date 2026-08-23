# 11. A third repair joins the comparison, and the default does not move

Date: 2026-08-22

## Status

Accepted. Amends the measurement described in ADR 0007; changes no decision in it.

## Context

ADR 0005 repairs an invalid published polygon before any containment question is asked
of it, and ADR 0007 measures what that repair is worth by running `make_valid` and
`buffer(0)` to completion over the same records and counting the disagreement: 927
records, 0.70% of the record set, come out differently.

Two repairs bound the ambiguity from two sides. GEOS carries a third reading of an
invalid polygon: its structure-preserving repair, exposed in Shapely as
`make_valid(geometry, method="structure")`. Where rings overlap or nest, it answers
differently from the noding repair this project uses: on a shell overlapped by one of
its own holes, the noding reading produces a multipolygon of area 100 while the
structure reading produces a single polygon of area 70. This record set contains
nested-shell failures, which is precisely the shape the two readings disagree about.

## Decision

`make_valid_structure` joins `REPAIR_STRATEGIES`, and the sensitivity run places the
whole record set under every strategy in that tuple. The published comparison gains:

- a pairwise disagreement count for each of the three pairs,
- a union count, records where at least one pair disagrees, which bounds how much of
  the result the choice of repair can move,
- unusable counts per strategy, since a repair that collapses a polygon removes a
  territory from that run's index.

The default stays `make_valid`. Nothing in this change selects a winner among the
three; all three are answers to a question the published geometry does not settle, and
the point of running them together is to publish the size of the gap instead of
arguing about which answer to prefer.

## Consequences

The committed `published/` tree still describes the two-repair run against the
2026-08-17 pin, because regenerating it requires re-acquisition; see the refresh
triggers in `PROVENANCE.md`. The next deliberate refresh publishes the three-repair
census over the real record set, and until then the fixture build exercises it on every
`make verify`.

A fourth repair would join the same way: add the strategy, add it to the sensitivity
run, and let the union count grow. What would make that change dishonest is shipping a
new default without exactly this measurement.
