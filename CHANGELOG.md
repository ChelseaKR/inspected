# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `inspected.sensitivity`: the two judgment calls in this project, re-run over the whole
  record set and published with their denominators and intervals rather than argued for.
  - **The inclusion rule.** Seven readings of the publisher's `Type` field, each one the
    entire record set placed again. Reading `CO-OP` and `Tribal` as service territories,
    the unreviewed half of the rule, is worth 0.065 percentage points on the headline;
    dropping `Tribal` changes nothing at all; dropping `CO-OP` would publish 1,406
    records as inside no published territory. Reading `CCA` as a territory would take the
    contested share to 56.3% and `ADMIN` to 74.4%. The rule is unchanged. See
    `docs/adr/0006`.
  - **The geometry repair.** `make_valid` and `buffer(0)` both run to completion. 927
    records, 0.70% of the record set with an interval of 0.66% to 0.75%, come out
    differently; 770 move from placed to contested and 157 are contested under both but
    between a different pair of outlines. The 0.1.0 note that the two disagreed on
    "roughly 770 placements" was a recollection and it missed those 157. See
    `docs/adr/0007`.
- Whether being unattributable is a property of the data or of the fire. 94.3% of the
  405 incidents in the record set fall entirely on one side of the contested line, with
  the contested share by incident year running from 0.0% to 92.5%. No trend is drawn
  through the years and the artifact says why: the territory layer is a single retrieval,
  so every year is measured against identical boundaries. See `docs/adr/0008`.
- That CEC documents none of the six `Type` values is stated in the output and in
  `PROVENANCE.md`, checked against the layer metadata, the FGDC record and the item
  resources on the retrieval date.

### Changed

- Containment narrows by bounding box and then tests against a prepared geometry, rather
  than calling `STRtree.query(predicate="intersects")`, which does not use a prepared
  geometry and re-walks every ring on every test. The full build runs in about 17 seconds
  doing nine placements of the record set where it took about 50 doing one. A test holds
  the two forms to identical answers, and every published figure is unchanged.
- An interval whose two ends round to the same string is now printed at more decimal
  places until they differ. `0.7% to 0.7%` reads as certainty.
- The repair strategy and the set of included types are parameters on
  `geometry.load_territories`. `geometry.repair` refuses a strategy that is not in
  `REPAIR_STRATEGIES`, so a new repair cannot be used before it has been compared against
  the one in force.
- The per-year record counts moved from a standalone `years` block into the new
  measurement, where each year carries both its record count and the classified count
  that is the denominator of its share.

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
