# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-08-17

First measurement. No tag cut.

### Added

- Placement coverage over CAL FIRE DINS against the California Energy Commission's
  published electric service territory outlines: how much of the wildfire record set
  falls inside exactly one territory, inside more than one, inside none, or carries a
  coordinate that cannot be used. Every share carries its denominator and a Wilson
  interval.
- A representativeness check between the placed and contested populations, with a
  Newcombe interval on the difference, so a reader can see whether the third of the
  record set that cannot be attributed resembles the two thirds that can.
- Per-territory counts in name order, with the share of each territory's placed records
  contributed by its single largest incident. No damage rate is published for any
  territory and no territory is ordered against another.
- Boundary-proximity bands at 100, 250, 500 and 1000 metres, operationalizing the
  publisher's statement that the boundaries are approximate.
- A geometry ledger naming the eight published polygons that arrive failing an OGC
  validity check, and measuring what share of the placed total depends on the repair.
- `artifacts.check_all`: publication rules enforced before anything is written. A rate
  without a denominator or an interval, a not-measured rate carrying a zero, a coordinate
  or parcel field, a collection long enough to be a record listing, a key that ranks or
  scores, or territory rows out of name order each refuse the write.
- Acquisition guards on top of the walk consumed from `perimeter`: the layer's own record
  count read before and after, identifiers required to be strictly increasing and unique,
  and nothing written when any of those fails.
- A schema guard on the retrieval, so a file fetched without `HAZARDTYPE` raises instead
  of filtering to zero fire records and producing an honest, empty, misleading report.

### Notes

- `perimeter` is consumed as a pinned git dependency rather than vendored. Its paged walk
  is the one this project uses for the damage inspections, and re-implementing it would
  mean re-implementing a defect that has already been found and fixed once.
- `data/raw/` is not in git and never will be.
