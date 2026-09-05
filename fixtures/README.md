# Fixtures

Hand-written, not sampled. Nothing in this directory is a slice of the real retrievals.

The DINS file carries structure-level records at their published coordinates, along with
site addresses, parcel numbers and assessed values. A "small sample for the tests" cut
from that file would put real structures into git for the convenience of a test suite.
These are invented instead: four square territories over empty desert, one deliberately
broken polygon, and a dozen records placed by hand at coordinates chosen to exercise
every branch of the classification.

The geography is arranged so each outcome has a case:

| Fixture territory | Type | Purpose |
|---|---|---|
| Alpha Electric Company | IOU | Ordinary containment, and the edge band |
| Beta Municipal Utility | POU | Overlaps Alpha, so records in the overlap are contested |
| Gamma Rural Cooperative | CO-OP | Ships as a bowtie, so the repair ledger has something in it |
| Delta Choice Energy | CCA | Overlaps Alpha entirely, and must be excluded by type |

and each record in `dins_sample.json` lands in exactly one of: one territory, more than
one, none, an unusable coordinate, or a hazard that is not fire.

The county names are invented too. Two counties that do not exist, and two records the
publisher's county cell is empty on, so the branch that keeps a record with no county
name out of the county cut and inside every other denominator is exercised by a build
rather than only by a unit test.

`county_boundaries_sample.geojson` is the same kind of invention: three square counties,
drawn so the coordinate-county comparison has an agreement, a disagreement, and a record
whose coordinate reaches no county at all. It feeds only that comparison; nothing here is
a boundary of any real county, and the real layer this fixture stands in for is named in
`PROVENANCE.md`.

`county_inspections_sample.json` stands in for a county's own inspection record set,
the one file this repository does not have. No California county's records are pinned,
hashed, or downloaded anywhere here, so this is invented like everything else in the
directory: five rows for the invented Sample County East, naming three fires. Held
against `dins_sample.json` it produces one fire both sets carry, one this project
records under Sample County West instead, one no record here names at all, and one this
project counts here that the county's set does not name, which is every outcome
`cross_check` can report. One row deliberately spells a fire `Sample  One`, with the
case and the spacing wrong, so the name folding is exercised by data rather than only
by a unit test.

`county_inspections_with_a_coordinate_sample.json` is the same file with a latitude and
a longitude added, and it exists to be refused. It is committed rather than built inside
a test because that refusal is the one that matters most: the county products that are
easiest to find are address-level and parcel-level, and a maintainer will meet this file
before they meet the rule.

`make report-offline` builds the whole pipeline over these files, and `make determinism`
builds it twice and compares the trees byte for byte.
