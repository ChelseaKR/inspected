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

`make report-offline` builds the whole pipeline over these files, and `make determinism`
builds it twice and compares the trees byte for byte.
