# Provenance

Three files, two publishers, one retrieval date. `src/inspected/sources.py` is the
reviewed record and `tests/test_provenance.py` asserts this document agrees with it, so
the two cannot drift apart.

None of this is affiliated with, endorsed by, or approved by CAL FIRE, the California
Energy Commission, or any electric utility.

## What was downloaded

| Source | Publisher | Features | Bytes | Retrieved |
|---|---|---:|---:|---|
| CAL FIRE Damage Inspection (DINS) Data | California Department of Forestry and Fire Protection | 132522 | 23924477 | 2026-08-17 |
| Electric Load Serving Entities (IOU & POU) | California Energy Commission | 53 | 11724721 | 2026-08-17 |
| Electric Load Serving Entities (Other) | California Energy Commission | 32 | 7397382 | 2026-08-17 |

SHA-256 of each written file:

- `dins_postfire.json` `289a12cf3a55e77ae420e20128ab3c94407cad55a9405abc2a9dad195dac0715`
- `else_iou_pou.geojson` `e805520e747de619c9a97d03f8d70c9125f44b6e6fb2c0067bc122b317f2260e`
- `else_other.geojson` `f6e6880c03c4e062aa6f0b2a69a66b74e7782ff62a2a3ce7e641efc4f0f7ffe3`

The files themselves are not in git. `data/raw/` is ignored. The DINS retrieval is
132,522 structure-level records at their published coordinates, and this repository
publishes counts.

## Endpoints and terms

**CAL FIRE DINS.** `POSTFIRE_MASTER_DATA_SHARE` layer 0, listed among the dataset's own
resources on [data.ca.gov](https://data.ca.gov/dataset/cal-fire-damage-inspection-dins-data).
Creative Commons Attribution.

**CEC Electric Load Serving Entities.** Two feature services published by the California
Energy Commission, ArcGIS Online items `30410214d637434ba1003cbdcc32cf55` and
`07224640a2fe42f89399be796e7b8810`, both last modified by the publisher 2026-08-12.
Terms: [CEC conditions of use](https://www.energy.ca.gov/conditions-of-use).

Seven DINS fields are requested and no others: `OBJECTID`, `DAMAGE`, `HAZARDTYPE`,
`INCIDENTNAME`, `INCIDENTSTARTDATE`, `LATITUDE`, `LONGITUDE`. `SITEADDRESS`, `APN`,
`STREETNUMBER`, `STREETNAME`, `ZIPCODE` and `ASSESSEDIMPROVEDVALUE` are published by CAL
FIRE, are not needed to answer which polygon a point is in, and are therefore never
downloaded. `tests/test_acquire.py` asserts that.

Requests carry a User-Agent naming this project, pause between pages, and stop rather
than route around a 401, 403 or 429. No agency website is crawled: three REST endpoints
are read the way their own dataset pages document them to be read.

## How completeness is established

Each layer is asked for its own record count before and after the walk. A walk that
disagrees with either writes nothing. Identifiers must come back strictly increasing and
unique. The DINS walk itself is `perimeter`'s, pinned to commit
`dac60195c50786f33f69a8fab70b6230894ed374`, and the checks above are applied to its
output rather than assumed of it.

## Two decisions that move the numbers

**The projection is pinned as a pipeline.** California Albers, GRS80, no datum step, so
no PROJ grid files are involved and the arithmetic is identical on any machine. A WGS84
coordinate is therefore treated as though it were on GRS80, a shift of roughly one to two
metres in California. Every distance published here is a band at 100 metres or wider.
`tests/test_geometry.py` checks the pipeline against EPSG:3310.

**Eight of the published polygons arrive invalid and are repaired.** Ring
self-intersections and nested shells. An invalid polygon answers a containment question
undefined rather than refusing it, so each is passed through `make_valid`, named in the
report, and flagged on its territory row. 91.7% of the placed records sit inside one of
those repaired polygons, because two of the eight are the two largest territories in the
state. Both repairs are then run to completion: 927 records, 0.70% of the record set,
come out differently under `buffer(0)`. The exposure and what it is worth are both
published. See `docs/adr/0007`.

## What the publisher does not document

The inclusion rule reads the CEC `Type` field, and CEC documents none of its six values.
As retrieved on 2026-08-17: the layer metadata carries no description on the `Type` field
and no coded-value domain, the FGDC record carries no entity and attribute section, and
no data dictionary is attached to either item. The published load serving entities page
the metadata points to names four categories in prose and does not name `Tribal` or
`ADMIN` at all.

This is recorded as a fact about the source rather than as a complaint, and it is why the
rule is published with its sensitivity: `docs/adr/0006` reports what each reading of the
field is worth in records. What the rule costs is measured. What each value means is
still the publisher's to say.

## Refresh

There is no cadence and no staleness SLA. The figures move when someone re-runs
`make acquire` by hand and commits the new `published/` tree, and the retrieval date on
every page says when that last happened.
