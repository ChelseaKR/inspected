# 3. A record inside two published outlines is reported, never awarded

Date: 2026-08-17

## Status

Accepted.

## Context

50,167 records, 37.9% of the wildfire record set, fall inside more than one published
territory outline. Every tie-break rule available is defensible-sounding and wrong:

- Award to the smallest polygon. Assumes the smaller entity is always the more specific,
  which is exactly what an overlay polygon violates.
- Award to the investor-owned utility. Encodes an assumption about who serves whom.
- Award to the first match. Depends on the order the publisher happens to return features
  in, and is invisible in the output.

Each would produce a complete-looking per-territory table with a hidden rule inside it,
and each would attribute tens of thousands of burned structures to a named company on the
strength of a guess.

## Decision

Contested is an outcome, published as a count with its denominator, alongside the
combination of outlines involved. It is never resolved. Every rate over placed records
states that its denominator is the placed population, so a reader can see what fraction of
the record set the rate is silent about.

A point lying exactly on a shared edge counts as inside both, so an edge case becomes
contested rather than being decided by a floating-point comparison.

## Consequences

The headline number is a negative result, and the README leads with it. Two things make
it more than a complaint: the combinations are named, so the overlaps are locatable in the
publisher's data and fixable at the source; and the destroyed share among contested
records is compared against the placed population with an interval on the difference, so
a reader learns whether the missing third is a biased third. On damage outcome it does
not appear to be.
